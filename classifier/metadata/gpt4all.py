import sqlite3
from gpt4all import GPT4All
from classifier.utils.config import DB_PATH

model_path = r"C:\Users\DELL\AppData\Local\nomic.ai\GPT4All\Meta-Llama-3-8B-Instruct.Q4_0.gguf"

gpt4all_model = GPT4All(model_path)

def generate_plot(franchiseRecord):
    # """
    # Generates a plot summary for the given franchise using GPT-4.

    # Args:
    #     franchiseRecord (dict): A dictionary containing franchise metadata.

    # Returns:
    #     str: The generated plot summary.
    # """
    # plots = []
    # with sqlite3.connect(DB_PATH) as conn:
    #     cursor = conn.cursor()
    #     cursor.execute("""
    #         SELECT filemetadata.plot
    #         FROM filemetadata
    #         JOIN filepaths ON filemetadata.file_id = filepaths.id
    #         JOIN filesteps ON filepaths.id = filesteps.filepath_id
    #         WHERE filesteps.parent = ?
    #     """, (franchiseRecord['classifications']['folder'],))
    #     plots = [row[0] for row in cursor.fetchall() if row[0]]

    # if not plots:
    #     return "No plots found for this franchise."

    # prompt = f"Generate a concise plot summary for the following franchise based on these plots: {plots}. Respond only with the summary, without explanations or commentary."

    # with GPT4All(model_path) as gpt4all_model:
    #     response = gpt4all_model.generate(prompt, max_tokens=150, temp=0.3, top_k=40, top_p=0.9)
    
    # return response.strip()
    pass

def generate_awards(franchiseRecord):
    # """
    # Generates awards information for the given franchise using GPT-4.

    # Args:
    #     franchiseRecord (dict): A dictionary containing franchise metadata.

    # Returns:
    #     str: The generated awards information.
    # """
    # awards = []
    # with sqlite3.connect(DB_PATH) as conn:
    #     cursor = conn.cursor()
    #     cursor.execute("""
    #         SELECT filemetadata.awards
    #         FROM filemetadata
    #         JOIN filepaths ON filemetadata.file_id = filepaths.id
    #         JOIN filesteps ON filepaths.id = filesteps.filepath_id
    #         WHERE filesteps.parent = ?
    #     """, (franchiseRecord['classifications']['folder'],))
    #     awards = [row[0] for row in cursor.fetchall() if row[0]]

    # if not awards:
    #     return "No awards data available for this franchise."

    # prompt = f"Provide only the total number of wins and nominations from the following awards data: {awards}. Format the response as 'Total: X wins & Y nominations' or 'Total Oscars: X Wins: Y Nominations: Z' with no extra text."

    # with GPT4All(model_path) as gpt4all_model:
    #     response = gpt4all_model.generate(prompt, max_tokens=50, temp=0.1, top_k=10, top_p=0.5)

    # return response.strip()
    pass
