class Generator:
    def __init__(self, model):
        self.model = model

    def generate_summary(self, media_content):
        # Logic to generate a summary using the model
        summary = self.model.summarize(media_content)
        return summary

    def generate_keywords(self, media_content):
        # Logic to generate keywords using the model
        keywords = self.model.extract_keywords(media_content)
        return keywords

    def generate_genre(self, media_content):
        # Logic to predict genre using the model
        genre = self.model.predict_genre(media_content)
        return genre

    def enhance_metadata(self, media_content):
        summary = self.generate_summary(media_content)
        keywords = self.generate_keywords(media_content)
        genre = self.generate_genre(media_content)

        enhanced_metadata = {
            'summary': summary,
            'keywords': keywords,
            'genre': genre
        }
        return enhanced_metadata