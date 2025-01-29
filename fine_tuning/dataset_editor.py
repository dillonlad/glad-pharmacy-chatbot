import json

# Reloading the necessary data after environment reset
file_path = 'pharmacy_opening_hours_500_variations_varied_context.json'
output_path = 'pharmacy_opening_hours_500_variations_varied_context_and_ans.json'

# Load the JSON file
with open(file_path, 'r') as file:
    data = json.load(file)

# Process the dataset to make answers specific and adjust `answer_start`
processed_data = []
for entry in data:
    context = entry["context"]
    question = entry["question"].lower()
    
    # Determine the specific answer based on the question
    if "calverton" in question and "close" in question and "saturday" in question:
        answer = "Calverton closes at 5pm on Saturdays."
    elif "lowdham" in question and "close" in question and "saturday" in question:
        answer = "Lowdham closes at 1pm on Saturdays."
    elif "calverton" in question and "open" in question and "weekday" in question:
        answer = "Calverton is open from 9am to 6pm on weekdays."
    elif "lowdham" in question and "open" in question and "weekday" in question:
        answer = "Lowdham is open from 9am to 6pm on weekdays."
    elif "sunday" in question:
        answer = "Both branches are closed on Sundays."
    elif "lowdham" in question and "saturday" in question:
        answer = "Lowdham is open from 9am to 1pm on Saturdays."
    elif "calverton" in question and "saturday" in question:
        answer = "Calverton is open from 9am to 5pm on Saturdays."
    elif "weekday" in question:
        answer = "Both branches are open from 9am to 6pm on weekdays."
    elif "holiday" in question:
        answer = "Holiday hours can be found here."
    else:
        # Default to a general answer if no specific match is found
        answer = context

    # Find the `answer_start` index
    answer_start = context.find(answer)
    if answer_start == -1:
        # If the specific answer isn't found in the context, set it to -1 (invalid case)
        answer_start = -1

    # Update the entry
    processed_entry = {
        "context": context,
        "question": entry["question"],
        "answer": answer,
        "answer_start": answer_start,
    }
    processed_data.append(processed_entry)

# Save the processed dataset
with open(output_path, 'w') as file:
    json.dump(processed_data, file, indent=4)

output_path
