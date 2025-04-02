import pytest
from unittest.mock import Mock, patch
from api.app.services.llm import LLMService
from api.tests.test_config import TestSettings

@pytest.fixture
def llm_service():
    with patch('api.app.services.llm.AutoModelForCausalLM.from_pretrained') as mock_model, \
         patch('api.app.services.llm.AutoTokenizer.from_pretrained') as mock_tokenizer, \
         patch('api.app.services.llm.get_settings', return_value=TestSettings()):
        # Mock model and tokenizer
        mock_model.return_value = Mock()
        mock_tokenizer.return_value = Mock()
        
        # Mock device and to() method
        mock_model.return_value.device = Mock()
        mock_model.return_value.to = Mock(return_value=mock_model.return_value)
        
        # Mock generate method
        mock_output = Mock()
        mock_output[0].tolist.return_value = [1, 2, 3]
        mock_model.return_value.generate.return_value = mock_output
        
        # Mock tokenizer methods
        mock_tokenizer.return_value.decode.return_value = "Question: Test prompt\nAnswer: Test response"
        mock_tokenizer.return_value.pad_token = None
        mock_tokenizer.return_value.eos_token = "eos"
        
        service = LLMService()
        return service

def test_llm_initialization(llm_service):
    """Test that LLM service initializes correctly."""
    assert llm_service.model_name == "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    assert llm_service.max_length == 100
    assert llm_service.temperature == 0.3
    assert llm_service.top_p == 0.7

def test_prompt_formatting(llm_service):
    """Test prompt formatting."""
    prompt = "What is the capital of France?"
    formatted_prompt = llm_service._format_prompt(prompt)
    assert formatted_prompt == f"Question: {prompt}\nAnswer:"

def test_response_cleaning(llm_service):
    """Test response cleaning."""
    prompt = "What is the capital of France?"
    response = "Question: What is the capital of France?\nAnswer: Paris is the capital of France.\nStudent: Wow!"
    cleaned_response = llm_service._clean_response(response, prompt)
    assert cleaned_response == "Paris is the capital of France."

@pytest.mark.asyncio
async def test_generate_response(llm_service):
    """Test response generation."""
    # Test response generation
    response = await llm_service.generate_response("Test prompt")
    assert response == "Test response" 