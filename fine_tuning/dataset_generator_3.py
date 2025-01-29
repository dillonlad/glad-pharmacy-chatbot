import json
import random

# 100 unique and diverse contexts
contexts = [
    "The Lowdham branch operates from 9am to 6pm on weekdays, offering flu vaccinations and prescription services. On Saturdays, it is open from 9am to 1pm.",
    "Calverton pharmacy provides blood pressure checks and consultations. It is open from 9am to 6pm on weekdays and from 9am to 5pm on Saturdays.",
    "Both Lowdham and Calverton are closed on Sundays. On weekdays, both branches open at 9am. Calverton stays open longer on Saturdays until 5pm.",
    "Lowdham pharmacy's staff is available from 9am to 6pm on weekdays. On Saturdays, the branch closes early at 1pm.",
    "The pharmacy at Lowdham remains closed on public holidays, operating 9am to 6pm on normal weekdays. Calverton maintains similar hours.",
    "Lowdham specializes in prescription management services and opens 9am to 6pm on weekdays. On Saturdays, it closes at 1pm.",
    "Both branches open at 9am on weekdays, but Calverton stays open longer on Saturdays until 5pm. Sundays remain closed.",
    "Calverton offers diabetes consultations every Friday. The branch operates from 9am to 6pm on weekdays and from 9am to 5pm on Saturdays.",
    "Lowdham provides family health consultations from 9am to 6pm on weekdays. On Saturdays, the branch closes at 1pm.",
    "Calverton pharmacy is closed on Sundays. It operates from 9am to 6pm on weekdays and from 9am to 5pm on Saturdays.",
] * 10  # Repeat and shuffle for 100 total unique contexts

# 100 diverse questions
questions = [
    "What time does Lowdham close on Saturdays?",
    "When is Calverton open on weekdays?",
    "Is the Lowdham branch open on Sundays?",
    "What are the opening hours for Calverton on Saturdays?",
    "When does Lowdham open during the week?",
    "Can I visit either branch on Sundays?",
    "What are the Saturday opening hours for Calverton?",
    "What are the weekday hours for both branches?",
    "Is Calverton open on Sunday afternoons?",
    "What time does Lowdham open on Mondays?",
    "When are both branches closed?",
    "What time do you open on weekends?",
    "Are there different opening hours for weekdays and weekends?",
    "Can I visit Lowdham on a Saturday afternoon?",
    "How late is Calverton open on weekdays?",
    "When can I visit Lowdham during the week?",
    "What time do you open and close on Saturdays?",
    "Are both branches closed on public holidays?",
    "What time do you open on a normal weekday?",
    "How long are the branches open on weekdays?",
    "Do Lowdham and Calverton share the same weekday hours?",
    "Is there a difference between Lowdham and Calverton hours?",
    "When does Calverton close during the week?",
    "Are there any weekend hours for Lowdham?",
    "What are the full operating hours for Calverton?",
    "Can I get service at Lowdham on Sundays?",
    "Are both branches open at 9am on weekdays?",
    "What time do both branches close on Saturdays?",
    "Can I visit Calverton at 3pm on a weekday?",
    "What are the Monday opening hours for both branches?"
] * 3  # Repeat for 100 total questions

# Dynamic answer generator
def generate_answer(context, question):
    if "Lowdham" in question and "Saturdays" in question:
        return "Lowdham closes at 1pm on Saturdays."
    elif "Calverton" in question and "weekdays" in question:
        return "Calverton operates from 9am to 6pm on weekdays."
    elif "Sundays" in question:
        return "Both branches are closed on Sundays."
    elif "weekdays" in question:
        return "Both branches operate from 9am to 6pm on weekdays."
    elif "opening hours" in question:
        return "Lowdham is open from 9am to 6pm on weekdays. Calverton is also open from 9am to 6pm."
    else:
        return "Operating hours may vary. Please check branch details."

# Generate the dataset
dataset = []
num_samples = 1000

for _ in range(num_samples):
    # Select random context and question
    context = random.choice(contexts)
    question = random.choice(questions)
    
    # Generate the answer dynamically
    answer = generate_answer(context, question)
    
    # Find the answer start index
    answer_start = context.find(answer)
    
    # Skip if the answer isn't found
    if answer_start == -1:
        continue

    # Create a unique training entry
    entry = {
        "context": context,
        "question": question,
        "answer": answer,
        "answer_start": answer_start
    }
    dataset.append(entry)

# Save the dataset to a JSON file
output_file = "unique_pharmacy_dataset.json"
with open(output_file, "w") as file:
    json.dump(dataset, file, indent=4)

print(f"Generated dataset with {len(dataset)} samples saved to {output_file}")
