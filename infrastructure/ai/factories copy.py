from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from sentence_transformers import SentenceTransformer
from domain.entities import RAGQuery, RAGResponse, Language
from config import config



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


class RAGSystem:
    """RAG system implementation"""
    
    def __init__(self, llm_model: AutoModelForCausalLM, tokenizer: AutoTokenizer, 
                 embedding_model: SentenceTransformer, config: Dict[str, Any]):
        self.llm_model = llm_model
        self.tokenizer = tokenizer
        self.embedding_model = embedding_model
        self.config = config
        self.retriever = None  # Will be set by dependency injection
        self.chunker = None    # Will be set by dependency injection
    
    def process_query(self, query: RAGQuery) -> RAGResponse:
        """Process a RAG query"""
        import time
        start_time = time.time()
        print("Processing RAG query:", query.query)
        
        # Retrieve relevant documents
        retrieved_chunks = self.retriever.retrieve(
            query.query, 
            top_k=query.top_k, 
            with_context_window=query.context_window
        )
        
        # Build prompt
        prompt = self._build_prompt(query, retrieved_chunks)
        print("Built prompt:", prompt)
        
        
        # Generate response
        answer = self._generate_response(prompt)
        print("Generated answer:", answer)
        
        processing_time = time.time() - start_time
        
        # Create response
        response = RAGResponse(
            answer=answer,
            sources=retrieved_chunks,
            processing_time=processing_time
        )
  
        # print("RAG response generated:", response.answer)
        return response
    
    def _build_prompt(self, query: RAGQuery, retrieved_chunks: list) -> str:
        """Build prompt for RAG"""
        context = []
        seen = set()
        total_length = 0
        max_tokens = self.config.get('max_context_tokens', config.ai.max_context_tokens)
        
        for chunk in retrieved_chunks:
            t = chunk["chunk_text"].strip()
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
        """Generate response using LLM"""
        dialogue_template = [{"role": "user", "content": prompt}]
        formatted_prompt = self.tokenizer.apply_chat_template(
            conversation=dialogue_template,
            tokenize=False,
            add_generation_prompt=True
        )

        inputs = self.tokenizer(formatted_prompt, return_tensors="pt")
        inputs = {k: v.to("cpu") for k, v in inputs.items()}  # always move to CPU
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

# Global factory instance (Singleton)
_ai_factory = HuggingFaceModelFactory()
_rag_factory = RAGModelFactory(_ai_factory)


def get_ai_factory() -> HuggingFaceModelFactory:
    """Get AI factory instance"""
    return _ai_factory


def get_rag_factory() -> RAGModelFactory:
    """Get RAG factory instance"""
    return _rag_factory 