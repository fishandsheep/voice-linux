from __future__ import annotations

from functools import lru_cache


def apply_triton_src_patch() -> None:
    """Patch openai-whisper Triton kernels for newer Triton runtimes."""
    try:
        import whisper.triton_ops as triton_ops
    except Exception:
        return

    if getattr(triton_ops, "_voice_simple_src_patch_applied", False):
        return

    triton = getattr(triton_ops, "triton", None)
    if triton is None:
        return
    tl = triton_ops.tl

    @lru_cache(maxsize=None)
    def median_kernel(filter_width: int):
        @triton.jit
        def kernel(y, x, x_stride, y_stride, BLOCK_SIZE: tl.constexpr):
            row_idx = tl.program_id(0)
            offsets = tl.arange(0, BLOCK_SIZE)
            mask = offsets < y_stride

            x_ptr = x + row_idx * x_stride  # noqa: F841
            y_ptr = y + row_idx * y_stride

            LOAD_ALL_ROWS_HERE  # noqa: F821
            BUBBLESORT_HERE  # noqa: F821
            tl.store(y_ptr + offsets, MIDDLE_ROW_HERE, mask=mask)  # noqa: F821

        kernel = triton.JITFunction(kernel.fn)
        src = kernel.src.replace(
            "    LOAD_ALL_ROWS_HERE",
            "\n".join(
                [
                    f"    row{i} = tl.load(x_ptr + offsets + {i}, mask=mask)"
                    for i in range(filter_width)
                ]
            ),
        )
        src = src.replace(
            "    BUBBLESORT_HERE",
            "\n\n".join(
                [
                    "\n\n".join(
                        [
                            "\n".join(
                                [
                                    f"    smaller = tl.where(row{j} < row{j + 1}, row{j}, row{j + 1})",
                                    f"    larger = tl.where(row{j} > row{j + 1}, row{j}, row{j + 1})",
                                    f"    row{j} = smaller",
                                    f"    row{j + 1} = larger",
                                ]
                            )
                            for j in range(filter_width - i - 1)
                        ]
                    )
                    for i in range(filter_width // 2 + 1)
                ]
            ),
        )
        src = src.replace("MIDDLE_ROW_HERE", f"row{filter_width // 2}")
        kernel._unsafe_update_src(src)
        return kernel

    triton_ops.median_kernel = median_kernel
    triton_ops._voice_simple_src_patch_applied = True
