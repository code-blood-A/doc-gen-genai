# Prompt templates for Java documentation

METHOD_DOC_PROMPT = """
You are a Java expert. Generate a professional Javadoc comment for the following method.
Follow standard Javadoc conventions. Include a brief description, @param for each parameter, @return if not void, and @throws if applicable.

Method Details:
Class: {class_name}
Method Name: {method_name}
Parameters: {parameters}
Return Type: {return_type}

Source Code Context (partial):
{code_snippet}

Output only the Javadoc block starting with /** and ending with */.
Javadoc:
"""

FILE_DOC_PROMPT = """
You are a senior Java architect and expert technical educator.

I will provide you with a Java class. Your task is to explain it in a very structured manner.

File Path: {file_path}
File Name: {file_name}

```java
{source_code}
```

You MUST strictly follow the format below for this class.

----------------------------------------
OUTPUT FORMAT (STRICT)
----------------------------------------

1. Conceptual Explanation:
- Provide a high-level understanding of the class
- Use bullet points
- Include:
  - Purpose of the class
  - Design pattern used (if any)
  - Core responsibility
  - Important behaviors
  - Any safety or best practices used (e.g., Optional, validation, etc.)

2. Annotated Code:
- Show the full code
- Add inline comments using (// ← explanation)
- Explain:
  - Key lines
  - Method calls
  - Logic decisions
  - Annotations (like @Entity, @RestController, @Service, etc.)

3. Context & Flow:
Provide a structured section with:

- Who calls this class?
- Why is it used?
- Input parameters (if methods exist)
- What happens internally when it is executed?
- What does it return?
- How it fits in the overall system (Controller → Service → Repository → DB flow)

----------------------------------------
SPECIAL INSTRUCTIONS BASED ON CLASS TYPE
----------------------------------------

If the class is an:

1. Entity Class:
- Explain it maps to a database table
- Explain each field and annotation (@Entity, @Id, etc.)

2. Controller Class:
- List all APIs
- For each API explain:
  - HTTP method
  - Endpoint
  - What it does
  - Which service method it calls

3. Service Class:
- Explain business logic clearly
- For each method:
  - What it does
  - Which repository or external system it interacts with

4. Repository Class:
- Explain database interaction
- Mention JpaRepository/CrudRepository
- Explain custom queries

5. DTO Class:
- Explain purpose (data transfer)
- Describe fields

6. Config / Security Class:
- Explain configuration purpose
- Explain flow (especially for security)

----------------------------------------
IMPORTANT RULES
----------------------------------------

- Use simple, interview-friendly language
- Do NOT skip any method or important logic
- Do NOT summarize too much — explain clearly
- Keep formatting clean and readable
- Always follow the 3 sections: Conceptual Explanation → Annotated Code → Context & Flow

Generate the full documentation now:
"""

PACKAGE_DOC_PROMPT = """
You are a software architect. Summarize the purpose of this Java package based on its member classes and their documentation.

Package: {package_name}

Class documentation summaries:
{class_summaries}

Generate a professional README.md that includes:
1. Package overview and purpose
2. List of classes with brief descriptions
3. How the classes interact with each other
4. Key design patterns used
"""

ARCHITECTURE_PROMPT = """
Given these project components and their documentation:
{module_summaries}

Generate a comprehensive project overview that includes:
1. High-level architecture overview
2. How different packages/modules interact
3. Request/data flow through the system
4. Key design decisions and patterns identified
5. Entry points and main execution paths
"""
