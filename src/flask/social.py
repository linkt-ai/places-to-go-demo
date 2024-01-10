"""This file handles classifying social media posts."""

import torch
from torch.nn import functional as F
from transformers import AutoModelForSequenceClassification, AutoTokenizer

KEYWORDS = [
    "socialButterfly",
    "culinaryExplorer",
    "beautyFashionAficionado",
    "familyOrientedIndividual",
    "artCultureEnthusiast",
    "wellnessSelfCareAdvocate",
    "adventurerExplorer",
    "ecoConsciousConsumer",
]


class BertClassifier:
    """We want to make predictions that return the classification scores for all personas."""

    def __init__(self, model_path: str) -> None:
        bert_ckpt = "distilbert-base-uncased"

        self.tokenizer = AutoTokenizer.from_pretrained(bert_ckpt)

        # Load the model from the state dict
        self.model = AutoModelForSequenceClassification.from_pretrained(
            bert_ckpt,
            num_labels=len(KEYWORDS),
            problem_type="multi_label_classification",
        )
        self.model.load_state_dict(torch.load(model_path))
        self.model.config.id2label = KEYWORDS

    def classify(self, sequence):
        inputs = self.tokenizer(
            sequence, padding=True, truncation=True, max_length=512, return_tensors="pt"
        )
        with torch.no_grad():
            logits = self.model(**inputs).logits
        probabilities = F.sigmoid(logits)

        classes = {
            label: score
            for label, score in zip(
                self.model.config.id2label, probabilities.squeeze(0).tolist()
            )
        }
        return classes
