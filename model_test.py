from transformers import pipeline, AutoTokenizer, AutoModelForQuestionAnswering

def test_model(model_path, context, question):
    # Load the fine-tuned model and tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForQuestionAnswering.from_pretrained(model_path)

    # Initialize the question-answering pipeline
    qa_pipeline = pipeline("question-answering", model=model, tokenizer=tokenizer)

    # Perform QA on the given context and question
    result = qa_pipeline({"context": context, "question": question})

    return result

# Main execution
if __name__ == "__main__":
    # Path to the fine-tuned model directory
    fine_tuned_model_path = "./qa_model"  # Replace with the path to your fine-tuned model

    # Example context and question
    context = (
        "The Calverton branch is open from 9:00 AM to 6:00 PM on weekdays. The Calverton branch is open until 5:00 PM on Saturdays. The Calverton branch is closed on Sundays."
    )
    question = "Is the Calverton branch open on Sundays?"

    # Test the fine-tuned model
    answer = test_model(fine_tuned_model_path, context, question)

    print(f"Question: {question}")
    print(f"Answer: {answer['answer']}")
    print(f"Score: {answer['score']}")
