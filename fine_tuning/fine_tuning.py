from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForQuestionAnswering, TrainingArguments, Trainer
import torch

# Load the dataset
dataset = load_dataset("json", data_files="pharmacy_data_2 copy.json")

# Load the tokenizer and model
model_name = "distilbert-base-cased"
model = AutoModelForQuestionAnswering.from_pretrained(model_name)

# Tokenize the dataset

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")

def preprocess_function(examples):
    questions = examples["question"]
    contexts = examples["context"]
    answers = examples["answer"]
    answer_starts = examples["answer_start"]

    print(answers[0])
    
    # Tokenize the inputs
    inputs = tokenizer(questions, contexts, truncation=True, max_length=512, padding="max_length", return_tensors="pt")
    
    # Compute start and end positions
    start_positions = []
    end_positions = []

    for i_ans in range(len(answers)):
        # Handle examples with no answer
        if answer_starts[i_ans] is None:
            start_positions.append(torch.tensor(-1))  # Assign special token
            end_positions.append(torch.tensor(-1))
        else:
            # Find the tokenized start and end positions
            start_idx = answer_starts[i_ans]
            end_idx = start_idx + len(answers[i_ans])

            print(end_idx)
            
            # Map character positions to token positions
            token_start = inputs.char_to_token(i_ans, start_idx)
            token_end = inputs.char_to_token(i_ans, end_idx - 1)

            print(inputs)
            
            # Handle edge cases where tokenization fails
            if token_start is None:
                token_start = tokenizer.model_max_length
            if token_end is None:
                token_end = tokenizer.model_max_length
                print("##", token_end)
            
            start_positions.append(token_start)
            end_positions.append(token_end)
    
    # for i_ans in range(len(answers)):
    #     for i, answer in enumerate(answers[i_ans]["text"]):
    #         # Find the tokenized start and end positions
    #         start_idx = answers[i_ans]["answer_start"][i]
    #         end_idx = start_idx + len(answer)
            
    #         # Map character positions to token positions
    #         token_start = inputs.char_to_token(i, start_idx)
    #         token_end = inputs.char_to_token(i, end_idx - 1)
            
    #         # Handle edge cases where tokenization fails
    #         if token_start is None:
    #             token_start = tokenizer.model_max_length
    #         if token_end is None:
    #             token_end = tokenizer.model_max_length
            
    #         start_positions.append(token_start)
    #         end_positions.append(token_end)
    
    # Add positions to inputs
    inputs["start_positions"] = start_positions
    inputs["end_positions"] = end_positions
    
    return inputs

# Apply preprocessing
tokenized_dataset = dataset.map(preprocess_function, batched=True)
# Split the dataset into 90% train and 10% validation
train_test_split = tokenized_dataset["train"].train_test_split(test_size=0.1)

# Rename the splits for consistency
print(train_test_split)
split_dataset = {
    "train": train_test_split["train"],
    "validation": train_test_split["test"]
}

print(train_test_split["train"]["question"][0])
print(train_test_split["train"]["context"][0])
print(train_test_split["train"]["start_positions"][0])
print(train_test_split["train"]["end_positions"][0])
print(train_test_split["train"]["input_ids"][0])

print(dataset)

# Define training arguments
training_args = TrainingArguments(
    output_dir="./results",
    evaluation_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=16,
    num_train_epochs=5,
    weight_decay=0.01,
    logging_dir="./logs",
    save_total_limit=2
)

# Define the Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=split_dataset["train"],
    eval_dataset=split_dataset["validation"],
)
# Fine-tune the model
trainer.train()

# Save the model
trainer.save_model("./pharmacy_chatbot_model")
tokenizer.save_pretrained("./pharmacy_chatbot_model")
