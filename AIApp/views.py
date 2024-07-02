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
import tkinter as tk
from tkinter import filedialog, simpledialog
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




@api_view(['POST'])
def handle_user_choice(request,botid):
    try:
        user_choice = request.data.get('choice')
        
        if user_choice == '1':
            pdf_file = request.FILES.get('file')
            if pdf_file:
                description = select_and_read_pdf(pdf_file)
                UserDescription.objects.create(
                    botid=botid,
                    description=description,
                    url_data=None  # No URL data for choice 1
                )
                return JsonResponse({"text": description})
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
                UserDescription.objects.create(
                    botid=botid,
                    description=description,
                    url_data=None  # No URL data for choice 3
                )
                return JsonResponse({"description": description})
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
                botid=botid
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
    user_description = get_object_or_404(UserDescription, botid=botid)
    
    if user_description.train_status:
        return JsonResponse({'status': 'Bot is ready and trained.'})
    else:
        return JsonResponse({'status': 'Bot is not trained yet.'})  

@api_view(['POST'])
@csrf_exempt
def createbot(request,botid):
    user_description = get_object_or_404(
        UserDescription,

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
                model: Hello, I am Sam, your polite AI assistant. How can I assist you with the story of "The Runaway Clock" today?
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
        else:
            print("Invalid interaction style.")
            exit()
        history_list = []
        description_text = user_description.description
        max_tokens = 1000
        parts = split_text(description_text, max_tokens)
            
        for i, user_input in enumerate(parts, start=1):
                try:
                    print(f"Total parts to train {i}/{len(parts)}")
                    
                    if user_input is None:
                        print("No valid input provided.")
                        continue
                    
                    user_input_template = description + "\n" + user_input
                    
        
                    
                    chat_session = model.start_chat(
                        history=[
                            # Initialize chat history if needed
                        ]
                    )
                    
                    histroy_response = chat_session.send_message(user_input_template)
                    
                    conv = histroy_response.text
                    
                    formatted_conversation = []
                    
                    while not formatted_conversation:
                        # Split the conversation into individual interactions
                        interactions = conv.strip().split('\n\n')
                        
                        # Regex pattern to match roles and messages
                        pattern = re.compile(r'(\w+):\s*(.*)')
                        
                        for interaction in interactions:
                            parts = interaction.strip().split('\n')
                            for part in parts:
                                match = pattern.match(part.strip())
                                if match:
                                    role, message = match.groups()
                                    role = 'user' if role.lower() == 'user' else 'model'
                                    formatted_conversation.append({
                                        "role": role,
                                        "parts": [message]
                                    })
                        
                        if not formatted_conversation:
                            print("Formatted conversation is empty, trying again...")
                            chat_session = model.start_chat(
                                history=[
                                    # Initialize chat history if needed
                                ]
                            )
                            histroy_response = chat_session.send_message(user_input_template)
                            conv = histroy_response.text
                    
                    
                    history_list.extend(formatted_conversation)
                    
                except Exception as e:
                    print(f"Error in main loop: {e}")
            
            # Assuming you have a field named 'history_list' in your UserDescription model
        user_description.history_list = history_list
        user_description.train_status=True
        user_description.save()
            
        return Response({"message": "Conversation generation completed and history list saved successfully."}, status=200)
    except Exception as e:
        return Response({"error": f"Error in conversation generation or saving history list: {e}"}, status=500)

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import UserDescription

@api_view(['POST'])
@csrf_exempt
def chat_with_bot(request,botid):
    # Configure the API key
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
        print(f"Error configuring or initializing the generative model: {e}")
        exit()
    # Retrieve the UserDescription object based on uid, projectid, and botid
    user_description = get_object_or_404(
        UserDescription,
        botid=botid
    )

    # Check if train_status is True
    if user_description.train_status:
        try:
            # Initialize chat session with history_list if available
            chat_session = model.start_chat(
                history=user_description.history_list if user_description.history_list else []
            )
            # Get user input from POST request
            user_input = request.data.get('user_input', '')

            # Check if user wants to exit
            if user_input.lower() == "exit":
                return JsonResponse({'message': 'Session ended.'})

            # Send user input to the chat session
            response = chat_session.send_message(user_input)

            # Return AI response
            return JsonResponse({'response': response.text})

        except Exception as e:
            return JsonResponse({'error': f'Error in chat session: {str(e)}'}, status=500)

    else:
        return JsonResponse({'error': 'Bot is not trained yet.'}, status=400)