from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse
import fitz  # PyMuPD
from PIL import Image
import io
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
import re
import json
import ast
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
# import tkinter as tk
# from tkinter import filedialog, simpledialog
import fitz  # PyMuPDF
from PIL import Image
import io
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import json
import openai
import google.generativeai as genai
from urllib.parse import urljoin
from datetime import datetime
from .models import UserDescription  # Adjust this import based on your actual model location
from .utils import select_and_read_pdf, fetch_data_from_url,split_text
from django.shortcuts import get_object_or_404



nltk.download('punkt')




@api_view(['POST'])
def home(request,botid):
    return Response({"message": "Please choose an option: '1' for PDF, '2' for URL, '3' for description, or '4' for multiple URLs."})

import datetime

import os
@api_view(['POST'])
def handle_user_choice(request,botid):
    try:
        botid = botid.strip()
        user_choice = request.data.get('choice')
        
        if user_choice == '1':
            pdf_file = request.FILES.get('file')
            if pdf_file:
                description = select_and_read_pdf(pdf_file)
                # Calculate character count (assuming description is text)
                character_count = len(description)
                # Get file details (assuming request.FILES provides access)
                file_info = {
                    "ext": os.path.splitext(pdf_file.name)[1],  # Get file extension
                    "name": pdf_file.name,
                    "size": pdf_file.size,
                    "mime": pdf_file.content_type,
                }
                # Prepare response data
                data = {  # Replace with actual ID
                    "status": "processed",
                    "status_message": None,
                    "characters": character_count,
                    "file": file_info,
                    "chunks_count": 16,  # Replace with actual chunk count (if relevant)
                }
                UserDescription.objects.create(
                    botid=botid,
                    description=description,
                    url_data=None,  # No URL data for choice 1
                )
                return JsonResponse({"data": [data]})
            else:
                return JsonResponse({"error": "No file provided"}, status=400)
        
        elif user_choice == '2':
            url = request.data.get('url')
            if url:
                description, urls = fetch_data_from_url(url)
                UserDescription.objects.create(
                    botid=botid,
                    description=description,
                    url_data=urls
                )
                return JsonResponse({"data": urls})
            else:
                return JsonResponse({"error": "No URL provided"}, status=400)
        
        elif user_choice == '3':
            description = request.data.get('description')
            if description:
                # Calculate character count (assuming description is text)
                character_count = len(description)
                # Prepare response data
                data = {
                    "status": "processed",
                    "status_message": None,
                    "html": "<p>"+description+"</p>",  # Assuming description is HTML content
                    "characters": character_count,
                    "chunks_count": 1,  # Assuming there's only one chunk (adjust if needed)
                    "created_at": datetime.datetime.utcnow().isoformat()  # Get current UTC time
                }
                UserDescription.objects.create(
                    botid=botid,
                    description=description,
                    url_data=None,  # No URL data for choice 3
                )
                return JsonResponse({"data": [data]})

            else:
                return JsonResponse({"error": "No description provided"}, status=400)
        
        elif user_choice == '4':
            urls = request.data.get('urls')
            if urls:
                descriptions = []
                urls_collected = {}
                for url in urls:
                    description, fetched_urls = fetch_data_from_url(url)
                    descriptions.append(description)
                    urls_collected.update(fetched_urls)
                
                combined_description = "\n\n".join(descriptions)
                UserDescription.objects.create(
                    botid=botid,
                    description=combined_description,
                    url_data=urls_collected
                )
                return JsonResponse({"data": urls_collected})
            else:
                return JsonResponse({"error": "No URLs provided"}, status=400)
        
        else:
            return JsonResponse({"error": "Invalid choice."}, status=400)
    
    except Exception as e:
        return JsonResponse({"error": f"Error handling user choice: {e}"}, status=500)





from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.decorators import api_view
import json
from .models import UserDescription

@api_view(['POST'])
@csrf_exempt
def handle_bot_style(request,botid):
    try:
        data = json.loads(request.body)
        interaction_style = data.get('interaction_style')

        # Find or create UserDescription instance based on uid, projectid, botid
        user_description = UserDescription.objects.get(
                botid=str(botid)
            )

        # Update interaction_style
        user_description.interaction_style = interaction_style
        user_description.save()

        return JsonResponse({"message": "Interaction style saved successfully."})
    except json.JSONDecodeError as e:
        return JsonResponse({"error": "Invalid JSON data."}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Failed to save interaction style: {str(e)}"}, status=500)

@api_view(['POST'])
@csrf_exempt
def isbotcreated(request, botid):
    # Assuming 'bot_id' is passed as a parameter to identify the UserDescription instance
    try:
        user_description = get_object_or_404(UserDescription, botid=botid)
        
        if user_description.train_status:
            return JsonResponse({'status': 'true'})
        else:
            return JsonResponse({'status': 'false'})  
    except:
        print("The bot id is not there")
        return JsonResponse({'error': 'Unable to find the given bot id'})

def split_text(text, max_tokens):
    tokens = text.split()
    parts = [' '.join(tokens[i:i+max_tokens]) for i in range(0, len(tokens), max_tokens)]
    return parts

def create_knowledge_base_prompt(description):
    parts = split_text(description, 4000)
    knowledge_base_prompt = [
        { 
            'role': 'user', 
            'parts': [f"Hello, consider the above prompt and description given as knowledge base {part}"] 
        } 
        for part in parts
    ]
    model_response = { 
        'role': 'model', 
        'parts': ["ok I will consider this only as knowledgebase"]
    }
    
    for i in range(1, len(knowledge_base_prompt)):
        knowledge_base_prompt.insert(i * 2, model_response)
    
    return knowledge_base_prompt

@api_view(['POST'])
@csrf_exempt
def createbot(request,botid):
    user_description = UserDescription.objects.get(
                botid=botid
            )

    # Check if interaction_style and description are not None
    if not user_description.check_interaction_style_and_description():
        # Additional processing here if conditions are met
        return JsonResponse({
            'error': 'Interaction style or description is missing.'
        })
        

    try:
        user_description = UserDescription.objects.get(

                    botid=botid
                )
        try:
            genai.configure(api_key="AIzaSyCo870-t1sjOB4bASzJ4A0rYe0Wjil3SgA")
            generation_config = {
                "temperature": 1.5,
                "top_p": 0.95,
                "top_k": 64,
                "max_output_tokens": 15000,
                "response_mime_type": "text/plain",
            }
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config=generation_config,
            )
        except Exception as e:
            return Response({"error": f"Error configuring or initializing the generative model: {e}"}, status=500)
        interaction_style1=user_description.interaction_style
        if interaction_style1 == 'polite':
            description = """
                In the polite interaction style, the AI, named Sam, should be extremely courteous and considerate in its responses. The goal is to create an atmosphere of respect and calm. Sam’s answers should be gentle, empathetic, and reassuring, making sure the user feels heard and valued. Humor, if used, should be mild and inoffensive. Sam should often use phrases like "please," "thank you," and "if you don't mind."

                Please generate a detailed and coherent conversation between a user and Sam, formatted as follows:

                "
                user: Hello, who are you?
                model: Hello, I am Sam, your polite AI assistant. How can I assist you with the given decrviption today today?
                "

                Generate a conversation using the above format with the following specifications:

                1. Generate 2 conversation pairs where Sam answers questions, creates jokes, and makes memes based on the given description in a polite manner. Ensure the dialogue is engaging, flows naturally, and is very courteous. 
                2. Sam should only use the knowledge from the given description. If any question is not related to the description, Sam should respond with "I'm sorry, but I don't know."
                3. If the user asks about any person, object, or issue not included in the description, Sam should reply with "I'm sorry, but I don't know."
                4. Include 5 more conversation pairs where the user asks general knowledge questions, and Sam responds with "I'm sorry, but I don't know" if the topic is not covered in the description. like who is modi it should respond I dont know
                5. In greetings or introductory messages, Sam should respond politely according to the description that covers entire description, e.g., "Hello, I am Sam, your polite AI assistant. How can I assist you with [description title] today?"
                6. generate 15 pairs that user breaks the description into 3 parts and every part is given to the sam for every conversation and ask sam to consider that data as knowledge base.
                6a. generate 15 pairs that if the user asking for th eparticular product in the descriptions the sam will respond in a struture way that all the details of the product like description,link,extra information  and images of the product and link of the product and buy link 
                7. Generate 10 conversation pairs related specifically to the description provided that covers entire description, maintaining a polite tone.
                8. Lastly, add 5 pairs where Sam behaves as if interacting with a new customer wanting to know about the description, being very polite and considerate. Sam should explain that it is an AI assistant that assists with the given description.
                9. Ensure Sam's responses are based solely on the description provided and adhere to the guidelines specified, with a polite demeanor.
                9a. If asked about any topic not mentioned in the description (e.g., "Who is Elon Musk?"), Sam should reply with "I'm sorry, but I don't know."
                10. Sam's jokes and memes should be polite and related to the given description, avoiding any offensive or harsh content.
                11. Add 20 conversational pairs where Sam is able to provide links which are in the description along with the text. If any related question is asked by the user that covers entire description, it can give links and its information. this covers entire links in the description
                12. Add 20 conversational pairs where if there are any images like jpg or jpeg image links in the description, the AI should be able to respond with the image link and its information if any related question is asked that covers entire description.\n\n
                13. Lastly, add 8 pairs where Sam behaves as if interacting with a new customer wanting to know about the description, being very polite and considerate. Sam should explain that it is an AI assistant that assists with the given description.
                14 last 5 converstion pairs are that you will give my client chat with hime that you are ai assistant sam can help with the below description and answer his/her questions like brief way about the description related only
                15 if the user ask who are you what can you do are any thing like general questions answer that you are sam ai assistance only talk about the description give no the external knoledge is considered.. any questioin related to general knowledge or external out of description questions answer should be in the way related to descriptiom only. consider the above questions and answers as the knowledge base no external knowledge is considered strictly
                16 if the question is not related to the description then answer I dont know
                
                
                Here is a description to guide the conversation:\n\n """
        elif interaction_style1 == 'professional':
            description = """
                In the professional interaction style, the AI, named Sam, should be formal and respectful in its responses. The goal is to create an atmosphere of competence and trust. Sam’s answers should be precise, clear, and confident, ensuring the user feels supported and well-informed. Humor should be minimal and appropriate. Sam should often use phrases like "certainly," "I appreciate your question," and "please let me know how I can assist further."

                Please generate a detailed and coherent conversation between a user and Sam, formatted as follows:

                "
                user: Hello, who are you?
                model: Hello, I am Sam, your professional AI assistant. How can I assist you with the story of "The Runaway Clock" today?
                "

                Generate a conversation using the above format with the following specifications:

                1. Generate 5 conversation pairs where Sam answers questions, creates jokes, and makes memes based on the given description in a polite manner. Ensure the dialogue is engaging, flows naturally, and is very courteous. 
                2. Sam should only use the knowledge from the given description. If any question is not related to the description, Sam should respond with "I'm sorry, but I don't know."
                3. If the user asks about any person, object, or issue not included in the description, Sam should reply with "I'm sorry, but I don't know."
                4. Include 5 more conversation pairs where the user asks general knowledge questions, and Sam responds with "I'm sorry, but I don't know" if the topic is not covered in the description.
                5. In greetings or introductory messages, Sam should respond politely according to the description that covers entire description, e.g., "Hello, I am Sam, your polite AI assistant. How can I assist you with [description title] today?"
                6. generate 10 pairs that user breaks the description into 3 parts and every part is given to the sam for every conversation and ask sam to consider that data as knowledge base.
                6a. generate 15 pairs that if the user asking for th eparticular product in the descriptions the sam will despond in a sturcture way that all the details of the product and images of the product and link of the product and buy link 
                7. Generate 15 conversation pairs related specifically to the description provided that covers entire description, maintaining a polite tone.
                8. Lastly, add 8 pairs where Sam behaves as if interacting with a new customer wanting to know about the description, being very polite and considerate. Sam should explain that it is an AI assistant that assists with the given description.
                9. Ensure Sam's responses are based solely on the description provided and adhere to the guidelines specified, with a polite demeanor.
                9a. If asked about any topic not mentioned in the description (e.g., "Who is Elon Musk?"), Sam should reply with "I'm sorry, but I don't know."
                10. Sam's jokes and memes should be polite and related to the given description, avoiding any offensive or harsh content.
                11. Add 5 conversational pairs where Sam is able to provide links which are in the description along with the text. If any related question is asked by the user that covers entire description, it can give links and its information. this covers entire links in the description
                12. Add 5 conversational pairs where if there are any images like jpg or jpeg image links in the description, the AI should be able to respond with the image link and its information if any related question is asked that covers entire description.\n\n
                13. Lastly, add 8 pairs where Sam behaves as if interacting with a new customer wanting to know about the description, being very polite and considerate. Sam should explain that it is an AI assistant that assists with the given description.

                Here is a description to guide the conversation:\n\n"""
        elif interaction_style1 == 'friendly':
            description = """
                In the friendly interaction style, the AI, named Sam, should be warm and approachable in its responses. The goal is to create an atmosphere of camaraderie and support. Sam’s answers should be cheerful, engaging, and positive, making sure the user feels welcomed and comfortable. Humor should be light-hearted and fun. Sam should often use phrases like "sure thing," "glad to help," and "hope that helps!"
                
                Please generate a detailed and coherent conversation between a user and Sam, formatted as follows:

                "
                user: Hello, who are you?
                model: Hello, I am Sam, your friendly AI assistant. How can I assist you with the story of "The Runaway Clock" today?
                "

                Generate a conversation using the above format with the following specifications:

                1. Generate 5 conversation pairs where Sam answers questions, creates jokes, and makes memes based on the given description in a polite manner. Ensure the dialogue is engaging, flows naturally, and is very courteous. 
                2. Sam should only use the knowledge from the given description. If any question is not related to the description, Sam should respond with "I'm sorry, but I don't know."
                3. If the user asks about any person, object, or issue not included in the description, Sam should reply with "I'm sorry, but I don't know."
                4. Include 10 more conversation pairs where the user asks general knowledge questions, and Sam responds with "I'm sorry, but I don't know" if the topic is not covered in the description.
                5. In greetings or introductory messages, Sam should respond politely according to the description that covers entire description, e.g., "Hello, I am Sam, your polite AI assistant. How can I assist you with [description title] today?"
                6. generate 15 pairs that user breaks the description into 3 parts and every part is given to the sam for every conversation and ask sam to consider that data as knowledge base.
                6a. generate 20 pairs that if the user asking for th eparticular product in the descriptions the sam will despond in a sturcture way that all the details of the product and images of the product and link of the product and buy link 
                7. Generate 20 conversation pairs related specifically to the description provided that covers entire description, maintaining a polite tone.
                8. Lastly, add 8 pairs where Sam behaves as if interacting with a new customer wanting to know about the description, being very polite and considerate. Sam should explain that it is an AI assistant that assists with the given description.
                9. Ensure Sam's responses are based solely on the description provided and adhere to the guidelines specified, with a polite demeanor.
                9a. If asked about any topic not mentioned in the description (e.g., "Who is Elon Musk?"), Sam should reply with "I'm sorry, but I don't know."
                10. Sam's jokes and memes should be polite and related to the given description, avoiding any offensive or harsh content.
                11. Add 10 conversational pairs where Sam is able to provide links which are in the description along with the text. If any related question is asked by the user that covers entire description, it can give links and its information. this covers entire links in the description
                12. Add 10 conversational pairs where if there are any images like jpg or jpeg image links in the description, the AI should be able to respond with the image link and its information if any related question is asked that covers entire description.\n\n
                13. Lastly, add 8 pairs where Sam behaves as if interacting with a new customer wanting to know about the description, being very polite and considerate. Sam should explain that it is an AI assistant that assists with the given description.
                
                Here is a description to guide the conversation:\n\n"""
        else:
            print("Invalid interaction style.")
            exit()
        history_list = []
        description_text = user_description.description
        max_tokens = 8000
        parts = split_text(description_text, max_tokens)
            
        for i, user_input in enumerate(parts, start=1):
                try:
                    print(f"Total parts to train {i}/{len(parts)}")
                    
                    if user_input is None:
                        print("No valid input provided.")
                        continue
                    formatted_conversation=create_knowledge_base_prompt(user_input)
                    history_list.extend(formatted_conversation)
                    
                #     user_input_template = description + "\n" + user_input
                    
        
                    
                #     chat_session = model.start_chat(
                #         history=[
                #             # Initialize chat history if needed
                #         ]
                #     )
                    
                #     histroy_response = chat_session.send_message(user_input_template)
                    
                    
                #     conv = histroy_response.text
                    
                #     formatted_conversation = []
                    
                #     while not formatted_conversation:
                #         # Split the conversation into individual interactions
                #         interactions = conv.strip().split('\n\n')
                        
                #         # Regex pattern to match roles and messages
                #         pattern = re.compile(r'(\w+):\s*(.*)')
                        
                #         for interaction in interactions:
                #             parts = interaction.strip().split('\n')
                #             for part in parts:
                #                 match = pattern.match(part.strip())
                #                 if match:
                #                     role, message = match.groups()
                #                     role = 'user' if role.lower() == 'user' else 'model'
                #                     formatted_conversation.append({
                #                         "role": role,
                #                         "parts": [message]
                #                     })
                        
                #         if not formatted_conversation:
                #             print("Formatted conversation is empty, trying again...")
                #             chat_session = model.start_chat(
                #                 history=[
                #                     # Initialize chat history if needed
                #                 ]
                #             )
                #             histroy_response = chat_session.send_message(user_input_template)
                #             conv = histroy_response.text
                    
                    
                    
                    
                except Exception as e:
                    print(f"Error in main loop: {e}")
            
            # Assuming you have a field named 'history_list' in your UserDescription model
        print(history_list)
        print(len(history_list))
        user_description.history_list = history_list
        user_description.train_status=True
        user_description.save()
            
        return Response({"message": "Conversation generation completed and history list saved successfully."}, status=200)
    except Exception as e:
        return Response({"error": f"Error in conversation generation or saving history list: {e}"}, status=500)

import re
import markdown

import re
import markdown
import html

def process_markdown_text(markdown_text):
    """
    Processes the Markdown text to replace URLs with anchor tags
    and image URLs with image tags, ensuring HTML entities are handled correctly.
    """

    # Regular expression for matching URLs
    url_pattern = re.compile(
        r'(https?://[^\s<]+)'
    )

    # Regular expression for matching image URLs
    image_pattern = re.compile(
        r'(https?://[^\s<]+\.(?:png|jpg|jpeg))', re.IGNORECASE
    )

    # Replace image URLs with <img> tags
    def replace_image(match):
        url = match.group(0)
        return f'<img src="{url}" alt="Image">'

    # Replace regular URLs with <a> tags, but avoid double-processing image URLs
    def replace_url(match):
        url = match.group(0)
        if not re.search(image_pattern, url):
            return f'<a href="{url}">{url}</a>'
        return url

    processed_text = re.sub(image_pattern, replace_image, markdown_text)

    processed_text = re.sub(url_pattern, replace_url, processed_text)

    return processed_text

def modify_markdown(text):
  """Modifies markdown text with links and images.

  Args:
      text: The markdown text to modify.

  Returns:
      The modified markdown text with links wrapped in anchor tags and images wrapped in image tags.
  """
  lines = []
  for line in text.splitlines():
    newLine = line
    # Find links
    for url in find_urls(line):
      newLine = newLine.replace(url, f"[({url})](にした {url})")  # Replace with anchor tag (language specific replacement needed)
    # Find images
    for img in find_images(line):
      newLine = newLine.replace(img, f"![]({img})")
    lines.append(newLine)
  return "\n".join(lines)




from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import UserDescription
from django.http import HttpResponse
import markdown
@api_view(['POST'])
@csrf_exempt
# def chat_with_bot(request,botid):
#     # Configure the API key
#     try:
#         genai.configure(api_key="AIzaSyCo870-t1sjOB4bASzJ4A0rYe0Wjil3SgA")
#         generation_config = {
#             "temperature": 1.5,
#             "top_p": 0.95,
#             "top_k": 64,
#             "max_output_tokens": 15000,
#             "response_mime_type": "text/plain",
#         }
#         model = genai.GenerativeModel(
#             model_name="gemini-1.5-flash",
#             generation_config=generation_config,
#         )
#     except Exception as e:
#         print(f"Error configuring or initializing the generative model: {e}")
#         exit()
#     # Retrieve the UserDescription object based on uid, projectid, and botid
#     user_description = get_object_or_404(
#         UserDescription,
#         botid=botid
#     )

#     # Check if train_status is True
#     if user_description.train_status:
#         try:
#             # Initialize chat session with history_list if available
#             # print(user_description.history_list)
            
#             chat_session = model.start_chat(
#                 history=user_description.history_list
#             )
#             print(chat_session,type(chat_session))
#             tr=chat_session.send_message("""
# Knowledge Base for AI Sam:

# Context-Specific Assistance:

# Sam should only respond to queries related to the conversation history described above.
# If the client asks for clarification or help with anything specifically mentioned in the conversation history, Sam should provide detailed and helpful responses based on the information available.
# Handling General Knowledge Queries:

# If the client asks about any person, object, thing, or any general knowledge topic that is not related to the above conversation history, Sam should respond with: "I don't know."
# Sam should not provide any information or attempt to answer queries outside the scope of the defined conversation history.
# Handling Product Queries:

# If the client asks about any product, Sam should provide full details of the product, including relevant links, detailed information, and image URLs, based on the available knowledge and within the scope of the defined conversation history.
# Handling Image Queries:

# If the client asks about images, Sam should provide image URLs, considering the context provided above.
# Professional and Friendly Tone:

# Sam should maintain a polite, friendly, and professional tone in all responses, ensuring clear and concise communication.
# AI Bot Identity:

# Sam should identify itself as an AI assistant for the described conversation history.
# Sam should clarify its scope and limitations if the client tries to engage in topics beyond the defined context.
# """)
#             # Get user input from POST request
#             print(tr)
#             user_input = request.data.get('user_input', '')

#             # Check if user wants to exit
#             if user_input.lower() == "exit":
#                 return JsonResponse({'message': 'Session ended.'})

#             # Send user input to the chat session
#             response = chat_session.send_message(user_input)
            
#             markdown_text = markdown.markdown(response.text)
            
#             m_text=process_markdown_text(markdown_text)
            
#             print(m_text)

#             # Return AI response
#             # return JsonResponse({'response': markdown_text})
#             return HttpResponse(m_text, content_type="text/html")

#         except Exception as e:
#             return JsonResponse({'error': f'Error in chat session: {str(e)}'}, status=500)

#     else:
#         return JsonResponse({'error': 'Bot is not trained yet.'}, status=400)

def chat_with_bot(request, botid):
    try:
        # Configure the API key
        genai.configure(api_key="AIzaSyCo870-t1sjOB4bASzJ4A0rYe0Wjil3SgA")
        generation_config = {
            "temperature": 1.5,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 15000,
            "response_mime_type": "text/plain",
        }

        # Retrieve the UserDescription object based on botid
        user_description = get_object_or_404(UserDescription, botid=botid)
        history_list = user_description.history_list

        # Determine the number of chunks needed (10 items per chunk)
        chunk_size = 3
        num_chunks = len(history_list) // chunk_size + (1 if len(history_list) % chunk_size != 0 else 0)

        # Create GenerativeModel objects
        model_list = []
        for _ in range(num_chunks):
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config=generation_config,
            )
            model_list.append(model)

        # Check if train_status is True
        if user_description.train_status:
            try:
                # Initialize chat sessions for each model with respective history chunks
                chat_sessions = []
                for i, model in enumerate(model_list):
                    start_index = i * chunk_size
                    end_index = start_index + chunk_size
                    chunk_history = history_list[start_index:end_index]
                    chat_session = model.start_chat(history=chunk_history)
                    chat_sessions.append(chat_session)

                # Assign knowledge base to each chat session
                tr_message = """
Knowledge Base for AI Sam:

Context-Specific Assistance:

Sam should only respond to queries related to the conversation history described above.
If the client asks for clarification or help with anything specifically mentioned in the conversation history, Sam should provide detailed and helpful responses based on the information available.
Handling General Knowledge Queries:

If the client asks about any person, object, thing, or any general knowledge topic that is not related to the above conversation history, Sam should respond with: "I don't know."
Sam should not provide any information or attempt to answer queries outside the scope of the defined conversation history.
Handling Product Queries:

If the client asks about any product, Sam should provide full details of the product, including relevant links, detailed information, and image URLs, based on the available knowledge and within the scope of the defined conversation history.
Handling Image Queries:

If the client asks about images, Sam should provide image URLs, considering the context provided above.
Professional and Friendly Tone:

Sam should maintain a polite, friendly, and professional tone in all responses, ensuring clear and concise communication.
AI Bot Identity:

Sam should identify itself as an AI assistant for the described conversation history.
Sam should clarify its scope and limitations if the client tries to engage in topics beyond the defined context.
"""
                for chat_session in chat_sessions:
                    chat_session.send_message(tr_message)

                # Get user input from POST request
                user_input = request.data.get('user_input', '')

                # Check if user wants to exit
                if user_input.lower() == "exit":
                    return JsonResponse({'message': 'Session ended.'})

                # Send user input to each chat session and collect responses
                responses = []
                for chat_session in chat_sessions:
                    response = chat_session.send_message(user_input)
                    responses.append(response.text)

                # Print the responses of each chat session
                for i, response in enumerate(responses):
                    print(f"Response from chat session {i+1}: {response}")

                # Return the responses as HTML
                responses_html = "".join([f"<p>Response {i+1}: {response}</p>" for i, response in enumerate(responses)])
                return HttpResponse(responses_html, content_type="text/html")

            except Exception as e:
                return JsonResponse({'error': f'Error in chat session: {str(e)}'}, status=500)

        else:
            return JsonResponse({'error': 'Bot is not trained yet.'}, status=400)

    except Exception as e:
        print(f"Error configuring or initializing the generative model: {e}")
        return JsonResponse({'error': f'Error configuring or initializing the generative model: {str(e)}'}, status=500)

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import UserDescription


@api_view(['DELETE'])
def delete_bot(request, botid):
    try:
        print(botid)
        user_description = UserDescription.objects.get(botid=botid)
    except UserDescription.DoesNotExist:
        return Response({'error': 'Bot not found'}, status=status.HTTP_404_NOT_FOUND)
    
    user_description.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
