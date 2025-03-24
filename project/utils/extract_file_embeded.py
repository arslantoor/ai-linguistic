import openai
# Set your OpenAI API key
openai.api_key = "your-openai-api-key"  # Replace with your actual API key

def extract_file_embedding(file_content: str):
    """Extracts vector embeddings from file content using OpenAI's API."""
    try:
        # Generate embedding using OpenAI's text-embedding-ada-002 model
        response = openai.Embedding.create(
            input=file_content,
            model="text-embedding-ada-002"
        )
        # Extract the embedding from the response
        embedding = response['data'][0]['embedding']
        return embedding  # Return the embedding as a list
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None