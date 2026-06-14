import gradio as gr
import pysubs2
import re
import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from deep_translator.constants import BASE_URLS
from deep_translator.exceptions import RequestError, TooManyRequests, TranslationNotFound
from deep_translator.validate import is_empty, is_input_valid, request_failed

from app.abus_genuine import *
from app.abus_path import *
from app.abus_text import *
from app.abus_nlp_spacy import *

import structlog
logger = structlog.get_logger()

class DeepTranslator:
    def __init__(self) -> None:
        self.translator = GoogleTranslator(source='auto', target='en')
        self.languages_dict = GoogleTranslator().get_supported_languages(as_dict=True)
        
   
    def get_languages(self) -> list:
        capitalized_keys = [key.capitalize() for key in self.languages_dict.keys()]
        return capitalized_keys
    
    def get_language_code(self, language_name) -> str:
        search_name = language_name.lower()
        for key, value in self.languages_dict.items():
            if key.lower() == search_name:
                return value
        return "en"
    
    def get_language_value(self, language_name):
        search_name = language_name.lower()
        for key, value in self.languages_dict.items():
            if key.lower() == search_name:
                return key
        return None    

    def _google_translate(self, source_lang: str, target_lang: str, text: str, timeout: int = 30) -> str:
        source_code = self.get_language_code(source_lang)
        target_code = self.get_language_code(target_lang)

        if not is_input_valid(text, max_chars=5000):
            raise ValueError("Input text too long for Google Translate")

        text = text.strip()
        if source_code == target_code or is_empty(text):
            return text

        url_params = {
            "sl": source_code,
            "tl": target_code,
            "q": text,
        }
        response = requests.get(BASE_URLS["GOOGLE_TRANSLATE"], params=url_params, timeout=timeout)

        if response.status_code == 429:
            raise TooManyRequests()

        if request_failed(status_code=response.status_code):
            raise RequestError()

        soup = BeautifulSoup(response.text, "html.parser")
        element = soup.find("div", {"class": "t0"})
        response.close()

        if not element:
            element = soup.find("div", {"class": "result-container"})
            if not element:
                raise TranslationNotFound(text)

        translated = element.get_text(strip=True)
        if translated == text:
            return text
        return translated
    
  
    
    def translate_text(self, source_lang: str, target_lang: str, text: str, progress=None) -> str:
        logger.info(f"[abus_translate_deep.py] translate_text start: source={source_lang} target={target_lang}")
        # line 끝 마침표 확인인
        use_punctuation = AbusText.has_ending_marks([text])
        
        # 텍스트를 문장 단위로 분리
        sentences = AbusText.split_into_sentences(text, use_punctuation)
        sentences = sentences
        
        translated_sentences = []
        
        # 각 문장을 번역
        for sentence in self._progress_iter(progress, sentences, "Translating sentences..."):
            try:
                translated = self._google_translate(source_lang, target_lang, sentence)
                translated_sentences.append(translated)
                logger.debug(f"[abus_translate_deep.py] translate_text - {source_lang}: {sentence} -> {target_lang}: {translated}")
            except Exception as e:
                logger.error(f"Translation error: {e}")
                translated_sentences.append(sentence)  # 에러 발생 시 원본 문장 사용
        
        # 번역된 문장들을 다시 하나의 텍스트로 결합
        final_text = ' '.join(translated_sentences)
        return final_text

    def translate_file(self, source_lang: str, target_lang: str, subtitle_file_path: str, output_file_path: str, progress=None, preprocess_for_tts: bool = True):
        logger.info(
            "[abus_translate_deep.py] translate_file start: source=%s target=%s input=%s output=%s preprocess_for_tts=%s",
            source_lang,
            target_lang,
            subtitle_file_path,
            output_file_path,
            preprocess_for_tts,
        )
        tts_source_file = subtitle_file_path
        if preprocess_for_tts:
            tts_source_file = path_add_postfix(subtitle_file_path, f"-{source_lang}", ".srt")
            AbusSpacy.process_subtitle_for_tts(subtitle_file_path, tts_source_file)

        source_code = self.get_language_code(source_lang)
        target_code = self.get_language_code(target_lang)
        logger.debug(f"[abus_translate_deep.py] translate_file {source_code}: {subtitle_file_path} -> {target_code}: {output_file_path}")

        # Load subtitles using pysubs2
        full_subs = pysubs2.load(tts_source_file)
        subs = full_subs
        
        # 구두점이 없는 언어의 경우 각 자막을 개별적으로 번역
        for event in self._progress_iter(progress, subs, "Translate..."):
            if not event.text:
                continue
                
            text = event.plaintext
            try:
                translated_text = self._google_translate(source_lang, target_lang, text)
                if translated_text:
                    event.text = translated_text
                    logger.debug(f"[abus_translate_deep.py] translate_file : text       - {text}")
                    logger.debug(f"[abus_translate_deep.py] translate_file : translated - {translated_text}")                        
                else:
                    logger.warning(f"[abus_translate_deep.py] translate_file - Empty translation for: {text}")
            except Exception as e:
                logger.error(f"Translation error for text '{text}': {e}")
                # 에러 발생 시 원본 텍스트 유지

        # Save the translated subtitles
        subs.save(output_file_path)   
        if preprocess_for_tts and tts_source_file != subtitle_file_path:
            cmd_delete_file(tts_source_file)  

            
    @staticmethod
    def _progress_iter(progress, iterable, desc: str):
        if progress is None:
            return iterable
        return progress.tqdm(iterable, desc=desc)
