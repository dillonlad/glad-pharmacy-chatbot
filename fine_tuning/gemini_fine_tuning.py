import json
import os
import shutil
import boto3
from transformers import (
    AutoTokenizer,
    AutoModelForQuestionAnswering,
    TrainingArguments,
    Trainer,
    default_data_collator,
)
from datasets import Dataset, DatasetDict


def save_to_s3(local_dir, bucket_name, s3_prefix):
    s3 = boto3.client("s3")
    for root, dirs, files in os.walk(local_dir):
        for file in files:
            local_path = os.path.join(root, file)
            relative_path = os.path.relpath(local_path, local_dir)
            s3_path = os.path.join(s3_prefix, relative_path)
            s3.upload_file(local_path, bucket_name, s3_path)
    print(f"Model and tokenizer saved to s3://{bucket_name}/{s3_prefix}")

# Load the dataset
def load_dataset(file_path):
    with open(file_path, "r") as file:
        data = json.load(file)
    return data

# Preprocess the dataset for Hugging Face
def preprocess_data(dataset, tokenizer):
    processed_examples = {
        "input_ids": [],
        "attention_mask": [],
        "start_positions": [],
        "end_positions": [],
    }

    for entry in dataset:
        context = entry["context"]
        question = entry["question"]
        answer = entry["answer"]
        answer_start = entry["answer_start"]

        # Tokenize the input (combine question and context)
        tokenized_input = tokenizer(
            question,
            context,
            truncation=True,
            padding="max_length",
            max_length=384,
            return_offsets_mapping=True,
            return_tensors="pt",
        )

        # Determine token positions for start and end of the answer
        offsets = tokenized_input["offset_mapping"][0]  # First batch only
        input_ids = tokenized_input["input_ids"][0]  # First batch only

        start_pos = None
        end_pos = None
        for idx, (start, end) in enumerate(offsets):
            if start == answer_start:
                start_pos = idx
            if end == answer_start + len(answer):
                end_pos = idx
                break

        # Skip if positions are not found
        if start_pos is None or end_pos is None:
            continue

        # Append processed data
        processed_examples["input_ids"].append(input_ids)
        processed_examples["attention_mask"].append(tokenized_input["attention_mask"][0])
        processed_examples["start_positions"].append(start_pos)
        processed_examples["end_positions"].append(end_pos)

    return processed_examples

def load_dataset_from_s3(bucket_name, s3_key):
    # Initialize the S3 client
    s3 = boto3.client("s3")
    
    # Download the dataset file from S3 to a local temporary file
    s3.download_file(bucket_name, s3_key, "dataset.json")
    
    # Load the dataset from the local file
    with open("dataset.json", "r") as file:
        data = json.load(file)
    
    return data

# Fine-tuning function
def fine_tune_model(dataset_file, model_checkpoint="bert-base-uncased"):
    # Load the dataset
    raw_data = load_dataset_from_s3("gladbot-model", dataset_file)

    # Load the tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_checkpoint)

    # Preprocess the dataset
    processed_data = preprocess_data(raw_data, tokenizer)

    # Convert processed data into Hugging Face Dataset
    dataset = Dataset.from_dict(processed_data)
    dataset = DatasetDict({"train": dataset})

    # Load the pre-trained model
    model = AutoModelForQuestionAnswering.from_pretrained(model_checkpoint)

    # Define training arguments
    training_args = TrainingArguments(
        output_dir="./qa_model",
        evaluation_strategy="no",
        save_steps=500,
        learning_rate=2e-5,
        per_device_train_batch_size=8,
        num_train_epochs=3,
        weight_decay=0.01,
        logging_dir="./logs",
        logging_steps=10,
        save_total_limit=1,
    )

    # Create the Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"],
        tokenizer=tokenizer,
        data_collator=default_data_collator,
    )

    # Fine-tune the model
    trainer.train()

    # Save the fine-tuned model
    model.save_pretrained("./qa_model")
    tokenizer.save_pretrained("./qa_model")

    # Replace these with your bucket name and desired S3 prefix
    bucket_name = "gladbot-model"  # Update with your S3 bucket name
    s3_prefix = "v1/qa_model"       # Update with your desired S3 folder path

    # Upload the model and tokenizer to S3
    save_to_s3("./qa_model", bucket_name, s3_prefix)

    return "./qa_model"

# Main execution
if __name__ == "__main__":

    print("script running")
    # Path to your JSON dataset
    dataset_path = "v1/dataset.json"  # Replace with the path to your JSON file

    # Fine-tune the model
    model_path = fine_tune_model(dataset_path)

    print(f"Fine-tuned model saved to: {model_path}")
