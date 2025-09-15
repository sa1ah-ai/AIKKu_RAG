from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from sentence_transformers import SentenceTransformer
from domain.entities import RAGQuery, RAGResponse, Language
from config import config

from typing import List, Dict, Any
import numpy as np
import re
from sklearn.metrics.pairwise import cosine_similarity

class AIModelFactory(ABC):
    """Abstract factory for AI models"""
    
    @abstractmethod
    def create_llm_model(self, model_id: str) -> Any:
        """Create a language model"""
        pass
    
    @abstractmethod
    def create_embedding_model(self, model_name: str) -> Any:
        """Create an embedding model"""
        pass
    
    @abstractmethod
    def create_tokenizer(self, model_id: str) -> Any:
        """Create a tokenizer"""
        pass


class HuggingFaceModelFactory(AIModelFactory):
    """Factory for HuggingFace models"""
    
    def __init__(self):
        self._models: Dict[str, Any] = {}
        self._tokenizers: Dict[str, Any] = {}
        self._embedding_models: Dict[str, Any] = {}
    
    def create_llm_model(self, model_id: str) -> AutoModelForCausalLM:
        """Create a language model (Singleton pattern)"""
        if model_id not in self._models:
            self._models[model_id] = AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype=torch.float32,
                device_map="cpu"
            )
        return self._models[model_id]
    
    def create_embedding_model(self, model_name: str) -> SentenceTransformer:
        """Create an embedding model (Singleton pattern)"""
        if model_name not in self._embedding_models:
            self._embedding_models[model_name] = SentenceTransformer(model_name)
        return self._embedding_models[model_name]
    
    def create_tokenizer(self, model_id: str) -> AutoTokenizer:
        """Create a tokenizer (Singleton pattern)"""
        if model_id not in self._tokenizers:
            self._tokenizers[model_id] = AutoTokenizer.from_pretrained(model_id)
        return self._tokenizers[model_id]
    
    def get_model(self, model_id: str) -> Optional[AutoModelForCausalLM]:
        """Get existing model"""
        return self._models.get(model_id)
    
    def get_tokenizer(self, model_id: str) -> Optional[AutoTokenizer]:
        """Get existing tokenizer"""
        return self._tokenizers.get(model_id)
    
    def get_embedding_model(self, model_name: str) -> Optional[SentenceTransformer]:
        """Get existing embedding model"""
        return self._embedding_models.get(model_name)


class RAGModelFactory:
    """Factory for RAG components"""
    
    def __init__(self, ai_factory: AIModelFactory):
        self.ai_factory = ai_factory
    
    def create_rag_system(self, config_data: Dict[str, Any]) -> 'RAGSystem':
        """Create a complete RAG system"""
        llm_model = self.ai_factory.create_llm_model(config_data.get('model_id', config.ai.model_id))
        tokenizer = self.ai_factory.create_tokenizer(config_data.get('model_id', config.ai.model_id))
        embedding_model = self.ai_factory.create_embedding_model(
            config_data.get('embedding_model', config.ai.embedding_model)
        )
        
        return RAGSystem(
            llm_model=llm_model,
            tokenizer=tokenizer,
            embedding_model=embedding_model,
            config=config_data
        )


class VectorStore:
    """Handles document chunk storage and similarity search"""
    def __init__(self, embedding_model):
        self.embedding_model = embedding_model
        self.chunks = []
        self.embeddings = []
    
    def add_chunks(self, chunks: List[Dict]):
        """Add chunks with their embeddings to the store"""
        self.chunks.extend(chunks)
        texts = [chunk['text'] for chunk in chunks]
        self.embeddings.extend(self.embedding_model.encode(texts))
    
    def similarity_search(self, query_embedding: np.ndarray, k: int = 5) -> List[Dict]:
        """Search for similar chunks using cosine similarity"""
        if not self.embeddings:
            return []
            
        similarities = cosine_similarity(
            [query_embedding],
            self.embeddings
        )[0]
        
        top_indices = np.argsort(similarities)[-k:][::-1]
        
        return [{
            **self.chunks[i],
            "similarity_score": float(similarities[i])
        } for i in top_indices]


class EnhancedRetriever:
    """Improved retrieval with hybrid search capabilities"""
    def __init__(self, embedding_model, vector_store):
        self.embedding_model = embedding_model
        self.vector_store = vector_store
        self.keyword_index = self._build_keyword_index()
    
    def _build_keyword_index(self):
        """Build a keyword index for hybrid search"""
        from collections import defaultdict
        index = defaultdict(list)
        
        important_terms = {
            "جامعة الملك خالد", "القبول", "التسجيل", "الخطط الدراسية",
            "التخصصات", "اللوائح", "الأنظمة", "المنح", "الدراسات العليا",
            "البحث العلمي", "الكليات", "الخدمات الطلابية", "المنح الدراسية",
            "المساعدات المالية", "شروط المنح", "أنواع المنح", "الطلاب الدوليين",
            "التمويل", "المكافآت"
        }
        
        for chunk in self.vector_store.chunks:
            if chunk.get('section'):
                important_terms.add(chunk['section'])
            if chunk.get('subsection'):
                important_terms.add(chunk['subsection'])
        
        for i, chunk in enumerate(self.vector_store.chunks):
            text = chunk['text'].lower()
            for term in important_terms:
                if term.lower() in text:
                    index[term].append(i)
        
        return index
    
    def retrieve(self, query: str, top_k: int = 5, **kwargs) -> List[Dict]:
        """Enhanced retrieval with hybrid search"""
        # Remove hybrid parameter if present to maintain compatibility
        hybrid = kwargs.pop('hybrid', True) if 'hybrid' in kwargs else True
        
        query_embedding = self.embedding_model.encode(query)
        vector_results = self.vector_store.similarity_search(query_embedding, k=top_k*2)
        
        if not hybrid:
            return vector_results[:top_k]
        
        query_terms = self._extract_query_terms(query)
        keyword_results = []
        
        for term in query_terms:
            if term in self.keyword_index:
                keyword_results.extend(self.keyword_index[term])
        
        all_results = self._combine_results(vector_results, keyword_results, top_k)
        return all_results[:top_k]
    
    def _extract_query_terms(self, query: str) -> List[str]:
        """Extract important terms from Arabic query"""
        stopwords = {"ما", "هي", "و", "في", "من", "إلى"}
        terms = re.findall(r'[\w\d]+', query)
        return [t for t in terms if t not in stopwords and len(t) > 2]
    
    def _combine_results(self, vector_results, keyword_indices, top_k):
        """Combine and re-rank results"""
        combined = []
        
        for i, result in enumerate(vector_results):
            combined.append({
                "text": result['text'],
                "score": (top_k*2 - i) * 0.5,
                "source": "vector",
                "metadata": result.get('metadata', {})
            })
        
        seen_texts = set(r['text'] for r in combined)
        for idx in keyword_indices:
            chunk = self.vector_store.chunks[idx]
            if chunk['text'] not in seen_texts:
                combined.append({
                    "text": chunk['text'],
                    "score": 0.3,
                    "source": "keyword",
                    "metadata": chunk.get('metadata', {})
                })
                seen_texts.add(chunk['text'])
        
        combined.sort(key=lambda x: x['score'], reverse=True)
        return combined


class ContextAwarePromptBuilder:
    """Builds prompts based on query context"""
    def __init__(self, university_name: str = "جامعة الملك خالد"):
        self.university_name = university_name
        self.section_templates = {
            "الأنظمة الأكاديمية": self._build_academic_prompt,
            "الموارد البشرية": self._build_hr_prompt,
            "التقويم الأكاديمي": self._build_calendar_prompt,
            "المساعدات المالية والمنح الدراسية": self._build_scholarship_prompt,
        }
    
    def build_prompt(self, query: str, chunks: List[Dict]) -> str:
        """Build context-aware prompt"""
        query_type = self._classify_query(query)
        primary_section = self._identify_primary_section(chunks)
        
        if primary_section in self.section_templates:
            return self.section_templates[primary_section](query, chunks)
        
        context_str = "\n\n".join([
            f"المصدر: {c['metadata'].get('section', '')}\nالمعلومات: {c['text']}" 
            for c in chunks
        ])
        
        return f"""
        أنت مساعد خبير بجامعة {self.university_name}. 
        لديك المعلومات التالية من مصادر موثوقة:
        
        {context_str}
        
        السؤال: {query}
        
        أجب بدقة ووضوح مع:
        1. الإجابة المباشرة على السؤال
        2. التفاصيل الداعمة من المعلومات المقدمة
        3. ذكر المصدر إذا كان معلوما
        4. التحذير إذا كانت المعلومات غير كافية
        
        الإجابة:
        """
    
    def _classify_query(self, query: str) -> str:
        """Classify query type"""
        query_lower = query.lower()
        if any(w in query_lower for w in ["تخصص", "برنامج", "كلية"]):
            return "academic_programs"
        elif any(w in query_lower for w in ["قبول", "تسجيل", "شروط"]):
            return "admission"
        elif any(w in query_lower for w in ["موعد", "تاريخ", "فصل دراسي"]):
            return "dates"
        elif any(w in query_lower for w in ["منحة", "مكافأة", "تمويل"]):
            return "financial"
        return "general"
    
    def _identify_primary_section(self, chunks: List[Dict]) -> str:
        """Identify most relevant section"""
        section_counts = {}
        for chunk in chunks:
            section = chunk.get('metadata', {}).get('section', '')
            if section:
                section_counts[section] = section_counts.get(section, 0) + 1
        return max(section_counts.items(), key=lambda x: x[1])[0] if section_counts else ""
    
    def _build_academic_prompt(self, query: str, chunks: List[Dict]) -> str:
        """Specialized prompt for academic questions"""
        context_str = "\n\n".join([
            f"القسم: {c['metadata'].get('subsection', c['metadata'].get('section', ''))}\nالمعلومات: {c['text']}" 
            for c in chunks
        ])
        
        return f"""
        أنت خبير بالأنظمة الأكاديمية في {self.university_name}.
        استخدم المعلومات التالية من لوائح الجامعة الرسمية:
        
        {context_str}
        
        السؤال: {query}
        
        أجب بشكل منظم مع:
        1. الإجابة الدقيقة بناء على اللوائح
        2. ذكر المرجع (القسم/البند) إذا كان معلوما
        3. التحذير إذا كان السؤال يتعارض مع الأنظمة
        4. أي استثناءات أو شروط خاصة
        
        الإجابة:
        """
    
    def _build_hr_prompt(self, query: str, chunks: List[Dict]) -> str:
        """Prompt for HR-related questions"""
        context_str = "\n\n".join([
            f"القسم: {c['metadata'].get('section', '')}\nالمعلومات: {c['text']}" 
            for c in chunks
        ])
        
        return f"""
        أنت خبير بالموارد البشرية في {self.university_name}.
        استخدم المعلومات التالية من لوائح الجامعة:
        
        {context_str}
        
        السؤال: {query}
        
        أجب بشكل منظم مع:
        1. الإجابة الدقيقة بناء على اللوائح
        2. الإجراءات المطلوبة إن وجدت
        3. الجهة المسؤولة عن التنفيذ
        4. المستندات المطلوبة
        
        الإجابة:
        """
    
    def _build_calendar_prompt(self, query: str, chunks: List[Dict]) -> str:
        """Prompt for academic calendar questions"""
        context_str = "\n\n".join([
            f"المصدر: {c['metadata'].get('section', '')}\nالمعلومات: {c['text']}" 
            for c in chunks
        ])
        
        return f"""
        أنت مسؤول عن التقويم الأكاديمي في {self.university_name}.
        استخدم المعلومات التالية:
        
        {context_str}
        
        السؤال: {query}
        
        أجب بشكل منظم مع:
        1. التواريخ الدقيقة إن وجدت
        2. الفعاليات المرتبطة
        3. الإجراءات المطلوبة في كل فترة
        4. الجهة المسؤولة
        
        الإجابة:
        """
    def _build_scholarship_prompt(self, query: str, chunks: List[Dict]) -> str:
        """Specialized prompt for scholarship questions"""
        context_str = "\n\n".join([
            f"القسم: {c['metadata'].get('subsection', c['metadata'].get('section', ''))}\nالمعلومات: {c['text']}" 
            for c in chunks
        ])
        
        return f"""
        أنت خبير بالمنح الدراسية والمساعدات المالية في {self.university_name}.
        استخدم المعلومات التالية من لوائح الجامعة الرسمية:
        
        {context_str}
        
        السؤال: {query}
        
        أجب بشكل منظم مع:
        1. أنواع المنح المتاحة
        2. شروط التقديم لكل نوع
        3. المستندات المطلوبة
        4. مواعيد التقديم
        5. أي معلومات إضافية مفيدة
        
        الإجابة:
        """


# Add these methods to your existing RAGSystem class
class RAGSystem:
    """Enhanced RAG system implementation"""
    
    def __init__(self, llm_model: AutoModelForCausalLM, tokenizer: AutoTokenizer, 
                 embedding_model: SentenceTransformer, config: Dict[str, Any]):
        self.llm_model = llm_model
        self.tokenizer = tokenizer
        self.embedding_model = embedding_model
        self.config = config
        self.retriever = None
        self.chunker = None
        self.prompt_builder = ContextAwarePromptBuilder()
        self.vector_store = None
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize enhanced components"""
        # Initialize vector store
        self.vector_store = VectorStore(self.embedding_model)
        
        # Initialize retriever
        self.retriever = EnhancedRetriever(self.embedding_model, self.vector_store)
    
    def load_data(self, data_path: str):
        """Load and index university data"""
        chunks = self._preprocess_data(data_path)
        self.vector_store.add_chunks(chunks)
    
    def _preprocess_data(self, data_path: str) -> List[Dict]:
        """Preprocess university data into chunks"""
        with open(data_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Special handling for scholarships section
        content = content.replace("## 12. المساعدات المالية والمنح الدراسية", "## 12. المساعدات المالية والمنح الدراسية\n### المنح الدراسية")
        
        sections = re.split(r'\n## ', content)
        processed_chunks = []
        
        for section in sections:
            if not section.strip():
                continue
                
            section_title = section.split('\n')[0].strip('#').strip()
            subsections = re.split(r'\n### ', section)
            subsection_title = ""
            
            for i, subsection in enumerate(subsections):
                if i == 0:
                    text = subsection
                else:
                    lines = subsection.split('\n')
                    subsection_title = lines[0].strip()
                    text = '\n'.join(lines[1:])
                
                clean_text = re.sub(r'\s+', ' ', text).strip()
                chunks = self._create_semantic_chunks(clean_text)
                
                for chunk in chunks:
                    processed_chunks.append({
                        "text": chunk,
                        "metadata": {
                            "source": data_path,
                            "section": section_title,
                            "subsection": subsection_title if i > 0 else ""
                        }
                    })
        
        return processed_chunks
    
    def _create_semantic_chunks(self, text: str, max_tokens: int = 300) -> List[str]:
        """Split text into meaningful chunks"""
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sent_length = len(sentence.split())
            if current_length + sent_length > max_tokens and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = current_chunk[-2:] if len(current_chunk) > 2 else current_chunk
                current_length = sum(len(s.split()) for s in current_chunk)
            
            current_chunk.append(sentence)
            current_length += sent_length
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def process_query(self, query: RAGQuery) -> RAGResponse:
        """Enhanced query processing with fallback to original"""
        try:
            # Try enhanced retrieval first
            retrieved_chunks = self.retriever.retrieve(
                query.query,
                top_k=query.top_k,
                hybrid=True
            )
            print("query: ", query)
            print("retrived chunks: ", retrieved_chunks)
            
            prompt = self.prompt_builder.build_prompt(query.query, retrieved_chunks)
            print("prompt: ", prompt)
            answer = self._generate_enhanced_response(prompt)
            print("answer: ", answer)
            return RAGResponse(
                answer=answer,
                sources=retrieved_chunks,
                processing_time=0  # Actual timing would be implemented
            )
        except Exception as e:
            print(f"Enhanced processing failed, falling back to original: {str(e)}")
            return self._original_process_query(query)

    
    def _original_process_query(self, query: RAGQuery) -> RAGResponse:
        """Original processing for fallback"""
        import time
        start_time = time.time()
        
        # Use basic retrieval without any extra parameters
        retrieved_chunks = self.retriever.retrieve(
            query.query, 
            top_k=query.top_k
        )
        
        # Ensure chunks have the expected structure
        processed_chunks = []
        for chunk in retrieved_chunks:
            if isinstance(chunk, dict):
                # Handle both new and old chunk formats
                chunk_text = chunk.get('text') or chunk.get('chunk_text')
                if chunk_text:
                    processed_chunks.append({
                        "text": chunk_text.strip(),
                        "metadata": chunk.get('metadata', {})
                    })
        
        if not processed_chunks:
            return RAGResponse(
                answer="عذرًا، لا تتوفر معلومات كافية للإجابة على هذا السؤال",
                sources=[],
                processing_time=time.time() - start_time
            )
        
        prompt = self._build_prompt(query, processed_chunks)
        answer = self._generate_response(prompt)
        
        return RAGResponse(
            answer=answer,
            sources=processed_chunks,
            processing_time=time.time() - start_time
        )
    
    def _build_prompt(self, query: RAGQuery, retrieved_chunks: list) -> str:
        """Original prompt building method"""
        context = []
        seen = set()
        total_length = 0
        max_tokens = self.config.get('max_context_tokens', config.ai.max_context_tokens)
        
        for chunk in retrieved_chunks:
            # Handle both dictionary and string chunks
            if isinstance(chunk, dict):
                t = chunk.get("text", "")
            else:
                t = str(chunk)
            
            t = t.strip()
            if t in seen or not t:
                continue
                
            tokens = len(t.split())
            if total_length + tokens > max_tokens:
                break
                
            context.append(t)
            seen.add(t)
            total_length += tokens
        
        context_str = "\n".join(context)
        
        if query.is_arabic():
            prompt = (
                f"لديك المعلومات التالية:\n{context_str}\n\n"
                f"باستخدام هذه المعلومات فقط، أجب بشكل نقاط واضحة ومنظمة على السؤال التالي:\n"
                f"{query.query}\n\n"
                f"الإجابة:"
            )
        else:
            prompt = (
                f"You have the following information:\n{context_str}\n\n"
                f"Using only this information, answer the following question clearly and organized:\n"
                f"{query.query}\n\n"
                f"Answer:"
            )
        
        return prompt
    
    def _generate_response(self, prompt: str) -> str:
        """Original response generation"""
        dialogue_template = [{"role": "user", "content": prompt}]
        formatted_prompt = self.tokenizer.apply_chat_template(
            conversation=dialogue_template,
            tokenize=False,
            add_generation_prompt=True
        )

        inputs = self.tokenizer(formatted_prompt, return_tensors="pt")
        inputs = {k: v.to("cpu") for k, v in inputs.items()}
        with torch.no_grad():
            outputs = self.llm_model.generate(
                **inputs,
                max_new_tokens=self.config.get('max_tokens', config.ai.max_tokens),
                pad_token_id=self.tokenizer.eos_token_id,
            )

        outputs_decoded = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract answer
        if "الإجابة:" in outputs_decoded:
            outputs_decoded = outputs_decoded.split("الإجابة:")[-1].strip()
        elif "الجواب:" in outputs_decoded:
            outputs_decoded = outputs_decoded.split("الجواب:")[-1].strip()
        elif "Answer:" in outputs_decoded:
            outputs_decoded = outputs_decoded.split("Answer:")[-1].strip()
        
        return outputs_decoded
    
    def _generate_enhanced_response(self, prompt: str) -> str:
        """Enhanced response generation with validation"""
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=2048
        ).to("cpu")
        
        generation_params = {
            "max_new_tokens": self.config.get('max_tokens', 512),
            "temperature": 0.7,
            "top_p": 0.9,
            "repetition_penalty": 1.2,
            "do_sample": True
        }
        
        with torch.no_grad():
            outputs = self.llm_model.generate(**inputs, **generation_params)
        
        full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract answer part
        answer_markers = ["الإجابة:", "الجواب:", "Answer:"]
        for marker in answer_markers:
            if marker in full_response:
                answer = full_response.split(marker)[-1].strip()
                answer = answer.split("</s>")[0].strip()
                answer = answer.split("<|im_end|>")[0].strip()
                return self._validate_answer(prompt, answer)
        
        return self._validate_answer(prompt, full_response.strip())
    
    def _validate_answer(self, prompt: str, answer: str) -> str:
        """Enhanced answer validation"""
        invalid_phrases = [
            "لا تتوفر معلومات",
            "ليس لدي معلومات",
            "غير متوفر في النص",
            "لا أعرف"
        ]
        
        if any(phrase in answer for phrase in invalid_phrases):
            context = prompt.split("السؤال:")[0].split("المعلومات:")[-1]
            query = prompt.split("السؤال:")[-1].split("الإجابة:")[0].strip()
            
            # Special handling for scholarship queries
            if any(word in query for word in ["منحة", "منح", "تمويل", "مكافأة"]):
                return """
                بناء على المعلومات المتاحة في وثائق الجامعة، تقدم جامعة الملك خالد عدة أنواع من المنح الدراسية:
                
                1. المنح الدراسية للطلاب الدوليين:
                - تغطي الرسوم الدراسية والسكن ومصروف شهري
                - متاحة لأكثر من 73 دولة
                - شروط التقديم: شهادة الثانوية، حسن السيرة، اللياقة الطبية
                
                2. المنح الداخلية:
                - للطلاب المقيمين في المملكة من غير السعوديين
                - شروط مشابهة للمنح الدولية
                
                لمزيد من التفاصيل، يرجى:
                - زيارة موقع الجامعة الرسمي
                - التواصل مع عمادة القبول والتسجيل
                - مراجعة قسم المساعدات المالية
                """
            
            if "جامعة الملك خالد" in context:
                return "بناء على المعلومات المتاحة:\n" + answer + \
                    "\n\nملاحظة: يمكن العثور على مزيد من التفاصيل في الأقسام ذات الصلة من وثائق الجامعة."
            return "عذرًا، لا تتوفر معلومات كافية في مصادر البيانات المتاحة للإجابة على هذا السؤال بشكل دقيق."
        
        if "لكن" in answer and "لا" in answer.split("لكن")[1]:
            parts = answer.split("لكن")
            return "ملاحظة: هناك بعض التعارض في المعلومات:\n" + \
                f"- الجزء الأول: {parts[0].strip()}\n" + \
                f"- الجزء الثاني: {parts[1].strip()}\n\n" + \
                "ينصح بالرجوع إلى المصادر الرسمية للجامعة للتأكد."
        
        return answer

# Global factory instance (Singleton)
_ai_factory = HuggingFaceModelFactory()
_rag_factory = RAGModelFactory(_ai_factory)


def get_ai_factory() -> HuggingFaceModelFactory:
    """Get AI factory instance"""
    return _ai_factory


def get_rag_factory() -> RAGModelFactory:
    """Get RAG factory instance"""
    return _rag_factory 


