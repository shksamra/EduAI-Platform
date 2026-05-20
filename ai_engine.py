import streamlit as st
import pdfplumber
import re
import json
import html
import torch
import numpy as np
import requests
from transformers import pipeline
from bs4 import BeautifulSoup
from transformers import AutoTokenizer, AutoModelForCausalLM
from googlesearch import search
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import TextIteratorStreamer
from threading import Thread


@st.cache_resource
# --- UPDATED AI ENGINE WITH FLAN-T5 ---

@st.cache_resource
def load_all_engines():
    # 1. Embedding Model (Stays the same)
    embed = SentenceTransformer('all-MiniLM-L6-v2')
    
    # 2. Optimized Quiz Model: Qwen 2.5 1.5B (Fast & Accurate)
    # No registration or login required. Works instantly.
    q_model_id = "Qwen/Qwen2.5-0.5B-Instruct"
    q_tok = AutoTokenizer.from_pretrained(q_model_id)
    q_mod = AutoModelForCausalLM.from_pretrained(
        q_model_id, 
        torch_dtype="auto", 
        device_map="auto"
    )
    
    # 3. NEW SUPER ACCURATE T5 (Flan-T5-Base)
    # This model is significantly more accurate for educational summaries
    s_model_name = "google/flan-t5-base" 
    s_tok = AutoTokenizer.from_pretrained(s_model_name)
    s_mod = AutoModelForSeq2SeqLM.from_pretrained(
        s_model_name, 
        torch_dtype="auto", 
        device_map="auto",
        low_cpu_mem_usage=True
    )
    
    return embed, q_tok, q_mod, s_tok, s_mod
def load_optimized_models():
    embed_model = SentenceTransformer('all-MiniLM-L6-v2')
    model_name = "Qwen/Qwen2.5-0.5B-Instruct"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype="auto", device_map="auto")
    return embed_model, tokenizer, model

with st.spinner("🚀 Booting High-Speed AI..."):
    embed_model, q_tok, q_mod = load_optimized_models()

def clean_section_text(text):
    noise_patterns = [r'MODULE\s+\d+.*', r'CHAPTER\s+\d+.*', r'Page\s+\d+.*']
    for pattern in noise_patterns:
        text = re.split(pattern, text, flags=re.IGNORECASE)[0]
    text = re.sub(r'\.{2,}', '.', text)
    return text.strip()

#-------------------------------------------------------------------------------PDF

def extract_pdf_index(file):
    full_text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            full_text += (page.extract_text() or "") + "\n"
    pattern = r'(\n\d+\.\d+\s+[A-Z].*)'
    parts = re.split(pattern, full_text)
    sections = {}
    if len(parts) < 2:
        sections["Full Content"] = clean_section_text(full_text)
    else:
        sections["Introduction"] = clean_section_text(parts[0])
        for i in range(1, len(parts), 2):
            raw_title = parts[i].strip()
            clean_title = re.sub(r'[\-\:\s\–\—]+$', '', raw_title)
            raw_content = parts[i+1].strip()
            clean_content = clean_section_text(raw_content)
            if len(clean_content) > 10: 
                sections[clean_title] = clean_content
    return sections


def stream_fast_abstractive_summary(text, q_tok, q_mod, level):
    # 1. Clean the PDF text
    clean_text = " ".join(text.split())
    if len(clean_text) < 10: 
        yield "This section does not contain enough text to summarize."
        return

    # 2. Strict Instruction Mapping
    if "Beginner" in level:
        role = "an elementary school teacher"
        style = "very simple language and easy analogies. Explain like I am 5."
    elif "Intermediate" in level:
        role = "a university professor"
        style = "academic language, focusing on definitions and core concepts."
    else: # Advanced
        role = "a senior technical researcher"
        style = "dense technical terminology, focusing on architecture and mechanisms."

    # 3. GROUNDED PROMPT (Updated to prompt for the format seen in your screenshot)
    # New Prompt for Paragraphs
    prompt = f"""[SOURCE TEXT]: {clean_text[:2000]}
[TASK]: Provide a detailed, cohesive summary for a {level} level student.
[INSTRUCTION]: Provide a summary in exactly 3 to 4 sentences only. Be extremely concise. 
Do NOT use bullet points or lists. Focus on explaining the core concepts in a narrative flow.
[LEARNING LEVEL]: {style}
[SUMMARY]:"""

    messages = [{"role": "user", "content": prompt}]
    
    # Generate Inputs
    text_input = q_tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    model_inputs = q_tok([text_input], return_tensors="pt").to(q_mod.device)

    # 4. STREAMER SETUP
    # skip_prompt=True handles the "Cleaning" by automatically removing the input text
    streamer = TextIteratorStreamer(q_tok, skip_prompt=True, skip_special_tokens=True)

    generation_kwargs = dict(
        **model_inputs,
        streamer=streamer,
        max_new_tokens=250,
        do_sample=False,        # Greedy is faster
        repetition_penalty=1.1,
        temperature=0.1,
        pad_token_id=q_tok.eos_token_id
    )

    # 5. START THREAD
    # Generation must happen in background so the main thread can "yield" words to UI
    thread = Thread(target=q_mod.generate, kwargs=generation_kwargs)
    thread.start()

    # 6. YIELD TOKENS
    for new_text in streamer:
        yield new_text

#--------------------------------------------------------------------------------WEB

def load_ai_engine():
    # BART model for summarization
    model_name = "sshleifer/distilbart-cnn-12-6"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    return tokenizer, model

tokenizer, model = load_ai_engine()

# --- HELPER FUNCTIONS ---
# Inside ai_engine.py

def fetch_web_text(url):
    try:
        # We add a timeout and headers to pretend we are a browser
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(f"https://r.jina.ai/{url.strip()}", timeout=15)
        if res.status_code == 200:
            content = html.unescape(res.text)
            if len(content.strip()) < 50: # If content is too short, it failed
                return "Error: Website returned no readable text."
            return content
        return f"Error: Could not reach site (Status {res.status_code})"
    except Exception as e:
        return f"Error: {str(e)}"

def process_long_summary(text, level, tok, mod): # Changed 'lvl' to 'level' for safety
    clean_text = " ".join(text.split())
    
    prompt = f"""[SOURCE TEXT]: {clean_text[:2000]}

[TASK]: Create a professional study guide for a {level} level student based ONLY on the source text.

[FORMATTING RULES]:
1. Use the following headers in BOLD (no hashtags):
   **DEFINITION**
   **KEY FEATURES**
   **PRACTICAL APPLICATIONS**
2. Use simple bullet points (-) for lists. 
3. Do NOT use nested numbers (no 1.1, 1.a, etc.).
4. Start each section on a new line.
5. If the information is not in the source text, do not invent it.

[SUMMARY]:"""

    messages = [{"role": "user", "content": prompt}]
    input_text = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    model_inputs = tok([input_text], return_tensors="pt").to(mod.device)

    streamer = TextIteratorStreamer(tok, skip_prompt=True, skip_special_tokens=True)
    
    generation_kwargs = dict(
        **model_inputs,
        streamer=streamer,
        max_new_tokens=800, # Increased for 3-4 paragraphs
        do_sample=False,
        repetition_penalty=1.1,
        temperature=0.1
    )
    
    thread = Thread(target=mod.generate, kwargs=generation_kwargs)
    thread.start()

    for new_text in streamer:
        yield new_text

def get_trending_blogs():
    return [
        {
            "title": "Mastering LLMs: A Guide for 2026",
            "url": "https://www.mooglelabs.com/blog/mastering-llm-ecosystem-ai-strategy-2026",
            "tag": "TRENDING"
        },
        {
            "title": "Building Scalable Microservices",
            "url": "https://medium.com/awsfullstack/scaling-microservices-a-comprehensive-guide-200737d75d62",
            "tag": "HOT"
        },
        {
            "title": "The Future of Quantum Computing",
            "url": "https://www.quantum-machines.co/blog/future-of-quantum-computing-quantum-experts-panel/",
            "tag": "NEW"
        },
        {
            "title": "React Server Components Explained",
            "url": "https://www.joshwcomeau.com/react/server-components/",
            "tag": "AI"
        },
        {
            "title": "Python Performance Optimization",
            "url": "https://blog.jetbrains.com/pycharm/2025/11/10-smart-performance-hacks-for-faster-python-code/",
            "tag": "CODE"
        }
    ]


#-------------------------------------------------------------------------------------QUIZ

def extract_major_sections(file):
    full_text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            full_text += "\n\n" + (page.extract_text() or "") + "\n\n"
    
    # Universal Regex: Matches 'MODULE 1:' or '1. Title' (ignoring 1.1)
    pattern = r'(\n(?:MODULE\s+\d+:|\d+\.(?!\d))\s+[A-Z].*)'
    parts = re.split(pattern, full_text)
    
    sections = {}
    if len(parts) < 2:
        sections["Full Document"] = clean_section_text(full_text)
    else:
        intro = clean_section_text(parts[0])
        if len(intro) > 150: sections["Introduction"] = intro
        for i in range(1, len(parts), 2):
            raw_title = parts[i].strip()
            clean_title = re.sub(r'[:\-—–\s]+$', '', raw_title) # Clean trailing junk
            content = clean_section_text(parts[i+1])
            if len(content) > 150: sections[clean_title] = content
    return sections 
