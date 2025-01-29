import json
import random

def find_sentence_with_substrings(context, substring1, substring2):
  """
  Finds the exact sentence in a given context that contains both specified substrings.

  Args:
    context: The input text.
    substring1: The first substring to search for.
    substring2: The second substring to search for.

  Returns:
    The sentence containing both substrings, or None if no such sentence is found.
  """

  lower_context = context.lower()

  sentences = context.split('. ')  # Split the context into sentences
  lowered_sentences = lower_context.split('. ')

  for index, sentence in enumerate(lowered_sentences):
    if substring1 in sentence and substring2 in sentence:
      return sentences[index]

  return None

def generate_contexts():
  """Generates 50 slightly varied versions of the context."""
  base_context = "Our branch in Lowdham is open from 9am to 6pm on weekdays. The Lowdham branch is open 9am to 1pm on Saturdays. The Lowdham branch is closed on Sundays. Our branch in Calverton is open 9am to 6pm on weekdays. The Calverton branch is open 9am to 5pm on Saturdays. The Calverton branch is closed on Sundays."
  variations = [
      "Our branch in Lowdham",
      "The Lowdham pharmacy",
      "Lowdham branch", 
      "Lowdham pharmacy", 
      "The Lowdham location" 
  ]
  contexts = []
  for _ in range(50):
    new_context = base_context
    for i in range(2):
      new_context = new_context.replace(variations[i], random.choice(variations))
    contexts.append(new_context)
  return contexts

def generate_questions(context):
  """Generates 10 unique questions based on the context."""
  questions = [
      "What are the opening hours of the Lowdham branch on weekdays?",
      "When does the Calverton branch close on Saturdays?",
      "Is the Lowdham branch open on Sundays?",
      "At what time does the Calverton branch open on weekdays?",
      "What are the Saturday opening hours for the Lowdham branch?",
      "On which days is the Calverton branch closed?",
      "When does the Lowdham branch open on Saturdays?",
      "What are the weekday opening hours for the Calverton branch?",
      "When does the Lowdham branch close on weekdays?",
      "What are the Saturday opening hours for the Calverton branch?",
      "When does the Lowdham branch open?",
      "When does the Calverton branch close?",
      "What are the opening hours for the Lowdham branch?",
      "What are the opening hours for the Calverton branch?",
      "Is either branch open on Sundays?",
      "Are both branches open on Saturdays?",
      "What are the weekday opening hours for the Lowdham branch?",
      "What are the weekday opening hours?",
      "What are the Saturday opening hours?",
      "What are the Sunday opening hours?"
  ]
  return random.sample(questions, 10)

def find_answer_start(context, answer):
  """Finds the starting index of the answer within the context."""
  return context.find(answer)

def generate_data():
  """Generates the list of 500 objects."""
  data = []
  contexts = generate_contexts()
  for context in contexts:
    questions = generate_questions(context)
    for question in questions:
      if question.lower().find("lowdham") != -1:
        if "weekdays" in question.lower():
          answer = find_sentence_with_substrings(context, "9am to 6pm", "lowdham")
        elif "saturdays" in question.lower():
          answer = find_sentence_with_substrings(context, "9am to 1pm", "lowdham")
        elif "sundays" in question.lower():
          answer = find_sentence_with_substrings(context, "closed", "lowdham")
        elif "open" in question.lower():
          answer = find_sentence_with_substrings(context, "9am", "lowdham")
        elif "close" in question.lower():
          answer = find_sentence_with_substrings(context, "6pm", "lowdham")
      elif question.lower().find("calverton") != -1:
        if "weekdays" in question.lower():
          answer = find_sentence_with_substrings(context, "9am to 6pm", "calverton")
        elif "saturdays" in question.lower():
          answer = find_sentence_with_substrings(context, "9am to 5pm", "calverton")
        elif "sundays" in question.lower():
          answer = find_sentence_with_substrings(context, "closed", "calverton")
        elif "open" in question.lower():
          answer = find_sentence_with_substrings(context, "9am", "calverton")
        elif "close" in question.lower():
          answer = find_sentence_with_substrings(context, "5pm", "calverton")
      else: 
        # Handle general questions (e.g., "What are the weekday opening hours?")
        if "weekdays" in question.lower():
          answer = find_sentence_with_substrings(context, "9am to 6pm" , "lowdham")
        elif "saturdays" in question.lower():
          answer = find_sentence_with_substrings(context, "saturdays", "lowdham")
        elif "sundays" in question.lower():
          answer = find_sentence_with_substrings(context, "closed" , "lowdham")
      answer_start = find_answer_start(context, answer)
      data.append({
          "context": context,
          "question": question,
          "answer": answer,
          "answer_start": answer_start
      })
  return data

if __name__ == "__main__":
  data = generate_data()
  with open("pharmacy_data_2.json", "w") as f:
    json.dump(data, f, indent=2)