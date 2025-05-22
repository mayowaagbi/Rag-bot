from ingest import load_documents_from_directory
from ingest import chunk_text

pdf_text = load_documents_from_directory(r"C:\Users\mayov\Downloads\project.pdf")
# print("\n=== PDF CONTENT ===\n")
# print(pdf_text[:1000])  # print first 1000 chars only

# docx_text = load_documents_from_directory(
#     r"C:\Users\mayov\Downloads\Online Learning System summary Agbi Olumayowa Olufemi.docx"
# )
# print("\n=== DOCX CONTENT ===\n")
# print(docx_text[:1000])

chugus = chunk_text(pdf_text, max_tokens=200, overlap=20)
print("\n=== CHUNKS ===\n")
print(chugus[:-1])
