from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "GPT4All-Community/Meta-Llama-3.1-8B-Instruct-128k-GGUF"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

from datasets import load_dataset

# Load your dataset
dataset = load_dataset('json', data_files='finetune_dataset.json')

# Tokenize the input-output pairs
def tokenize_function(examples):
    return tokenizer(examples['input'], truncation=True, padding="max_length", return_tensors="pt")

tokenized_datasets = dataset.map(tokenize_function, batched=True)

from transformers import Trainer, TrainingArguments

training_args = TrainingArguments(
    output_dir="./results",
    evaluation_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=2,
    per_device_eval_batch_size=2,
    num_train_epochs=3,
    weight_decay=0.01,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["test"],
)

trainer.train()

model.save_pretrained("./fine_tuned_mistral")
tokenizer.save_pretrained("./fine_tuned_mistral")

fine_tuned_model = AutoModelForCausalLM.from_pretrained("./fine_tuned_mistral")
fine_tuned_tokenizer = AutoTokenizer.from_pretrained("./fine_tuned_mistral")
