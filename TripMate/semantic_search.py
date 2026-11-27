import os
import math
from dotenv import load_dotenv
from google import genai
from google.genai import types

# initialization
load_dotenv()
api_key = os.getenv("GENAI_API_KEY")

if not api_key:
	raise ValueError("GENAI API KEY NOT FOUND!!")

client = genai.Client(api_key=api_key)
EMBEDDING_MODEL = "gemini-embedding-001"

# knowledge base
documents = [
	"Jaipur is famous for its historical forts and palaces.",
	"Hawa Mahal is a popular tourist attraction in Jaipur.",
    "Udaipur is known for its beautiful lakes and palaces.",
	"Jaipur has several popular markets selling traditional Rajasthani foor.",
	"Amer fort is located approximately 11km from Jaipur.",
	"Nahargarh Fort offers beautiful views of Jaipur city."
]

# generate document embeddings
def generate_document_embeddings(documents):
	response = client.models.embed_content(
		model = EMBEDDING_MODEL,
		contents = documents,
		config = types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
	)

	embeddings = [item.values for item in response.embeddings]

	return embeddings

#generate query embedding
def generate_query_embedding(query):
	response = client.models.embed_content(
		model = EMBEDDING_MODEL,
		contents=query,
		config=types.EmbedContentConfig(
			task_type="RETRIEVAL_QUERY"
		)
	)

	return response.embeddings[0].values

# cosine similarity
def cosine_similarity(a,b):
	dot_product = sum(x*y for x,y in zip(a,b))
	mag_a = math.sqrt(sum(x*x for x in a))
	mag_b = math.sqrt(sum(y*y for y in b))

	if mag_a == 0 or mag_b == 0:
		return 0.0
	return dot_product/(mag_a*mag_b)
# semantic search
def semantic_search(query,documents,document_embeddings, top_k=3):
	query_embedding = generate_query_embedding(query)
	results = []

	for document, doc_embedding in zip(documents,document_embeddings):
		score = cosine_similarity(
			query_embedding,
			doc_embedding
		)
		results.append(
			{
				"document":document,
				"similarity":score
			}		
		
		)

	# sort by similarity score in descending order
	results.sort(
		key = lambda x : x["similarity"],
		reverse = True
	)

	return results[:top_k]

# main execution
if __name__ == "__main__":
	print("Generating document embeddings...")
	document_embeddings = generate_document_embeddings(documents)
	print("Knowledge base ready")

	while True:
		query = input("\nSearch: ").strip()
		if query.lower() == "exit":
			break
		if not query:
			continue
		results = semantic_search(query,documents,document_embeddings,top_k=3)
		print("\n Most relevant results:")
		for result in results:
			print(f"\nSimilarity: {result['similarity']:.4f}")
			print(f"Document: {result['document']}")
	
	print("\nSearch session ended")
