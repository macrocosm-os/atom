import random
from typing import Any

import datasets
import nltk
from nltk.corpus import wordnet

from organic_scoring.synth_dataset import SynthDatasetBase

nltk.download("wordnet")


class SynthDatasetConversation(SynthDatasetBase):
    def __init__(self):
        """Samples LMSys dataset, requires to logging in to the HuggingFace."""
        self._url = "lmsys/lmsys-chat-1m"
        self.exception = None
        try:
            self.dataset = datasets.load_dataset(self._url)["train"]
        except Exception as e:
            self.exception = e
        self._chance_word_synonym = 0.10
        self._chance_char_typo = 0.02

    def sample(self) -> dict[str, Any]:
        """Sample the data, raises an exception if logging into HuggingFace was unsuccessful."""
        if self.exception is not None:
            raise self.exception
        # Randomly select a sample from the dataset.
        sample_idx = random.randint(0, len(self.dataset) - 1)
        conversation = self.dataset[sample_idx]["conversation"]
        roles = [entry["role"] for entry in conversation]
        messages = [entry["content"] for entry in conversation]

        # Randomly truncate the conversation.
        truncate_idx = random.randint(1, len(roles))
        roles = roles[:truncate_idx]
        messages = messages[:truncate_idx]

        # Ensure the conversation doesn't end with the assistant.
        if roles[-1] == "assistant":
            roles = roles[:-1]
            messages = messages[:-1]

        # Augment the messages by modifying words and introducing errors.
        messages = [self._augment_message(role, message) for role, message in zip(roles, messages)]

        return {"roles": roles, "messages": messages, "organic": False, "source": self._url}

    def _augment_message(self, role: str, message: str) -> str:
        if role == "assistant":
            return message

        words = message.split()
        num_words_to_modify = random.randint(1, max(1, int(len(words) * self._chance_word_synonym)))
        words_to_modify = random.sample(range(len(words)), num_words_to_modify)

        for idx in words_to_modify:
            synonym = self._get_synonym(words[idx])
            if synonym:
                words[idx] = synonym

        message = " ".join(words)
        message = self._introduce_typos(message)
        return message

    def _get_synonym(self, word: str) -> str:
        synonyms = wordnet.synsets(word)
        if synonyms:
            # Choose a synonym that is not the word itself.
            synonym_words = [lemma.name() for lemma in synonyms[0].lemmas() if lemma.name() != word]
            if synonym_words:
                return random.choice(synonym_words)
        return word

    def _introduce_typos(self, message: str) -> str:
        message = list(message)
        num_errors = random.randint(0, max(1, int(len(message) * self._chance_char_typo)))
        for _ in range(num_errors):
            error_type = random.choice(["remove", "add_space"])
            error_position = random.randint(0, len(message) - 1)

            if error_type == "remove":
                message.pop(error_position)
            elif error_type == "add_space":
                message.insert(error_position, " ")

        return "".join(message)
