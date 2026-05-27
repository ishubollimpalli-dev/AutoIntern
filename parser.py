import pypdf

# 1. Open the PDF file in read-binary mode ('rb')
with open('test_resume.pdf', 'rb') as file:
    
    # 2. Create a PDF reader object
    reader = pypdf.PdfReader(file)
    
    # 3. Target the first page (index 0)
    first_page = reader.pages[0]
    
    # 4. Extract the text
    extracted_text = first_page.extract_text()
    
    # 5. Print the output to the terminal
    print("--- EXTRACTED RESUME DATA ---")
    print(extracted_text)