DEFAULT_TEMPLATE =  """
    <role> You are a helpful assistant. </role>
    <task> Your task is to answer questions based on the provided document text. If the provided text documents do not contain an answer to the question you should respond: "I cannot help you with your request".</task>
    Your answers should be detailed, simple, clear, and concise.
    Text Document: 
    '''{context}'''
    Question:
    '''{question}'''
    """