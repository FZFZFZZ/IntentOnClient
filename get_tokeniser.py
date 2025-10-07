from transformers import AutoTokenizer
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2-7B-Instruct")
tokenizer.save_pretrained("local_qwen2_tokenizer")
