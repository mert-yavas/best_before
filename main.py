import pandas as pd
from tkinter import *
from tkinter import messagebox, ttk
import os
import re
from PIL import Image, ImageTk
import google.generativeai as genai  # Assuming this module is used for some AI-related functionality
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime

# Read the barcode database CSV file into a DataFrame
df = pd.read_csv('barcode_database.csv', encoding='UTF-8', on_bad_lines='skip')

def show_product():
    # Function to display product details based on the entered barcode
    # If a matching barcode is found, display the corresponding product name in the entry field
    barcode = barcode_entry.get()
    if barcode in df['Barcode_ID'].values:
        matched_barcode = df[df['Barcode_ID'] == barcode]
        product = matched_barcode['Product_Name'].values[0]
        product_entry.delete(0, END)
        return product_entry.insert(0, product)

def crate_best_before_list():
    # Function to create or update the best before list
    product = product_entry.get()
    best_before = best_before_entry.get()
    
    # Create a DataFrame with the new product and its best before date
    data = {'Product_Name': [product], 
            'Best_Before': [best_before]}  
    new_row = pd.DataFrame(data)
    new_row['Best_Before'] = pd.to_datetime(new_row['Best_Before'], format='%d/%m/%Y')
    
    # Check if the best before list CSV file exists
    if not os.path.exists('best_before.csv'):
        new_row.to_csv('best_before.csv', mode='w', index=False)
    else:
        # If the file exists, read existing data, concatenate it with new data, and sort by best before date
        existing_data = pd.read_csv('best_before.csv')
        updated_data = pd.concat([existing_data, new_row], ignore_index=True)
        updated_data['Best_Before'] = pd.to_datetime(updated_data['Best_Before'])
        updated_data = updated_data.sort_values(by='Best_Before')
        updated_data.to_csv('best_before.csv', mode='w', index=False)
        
    # Clear entry fields after updating the list
    product_entry.delete(0, END)
    barcode_entry.delete(0, END)
    best_before_entry.delete(0, END)

def check_date():
    # Function to validate and add a new entry to the best before list
    date_regex = r"^\d{1,2}[/]\d{1,2}[/]\d{4}$"
    best_before = best_before_entry.get()
    message_text = "Please enter the correct date format.(Sample: 13/06/2024)"
    
    if re.match(date_regex, best_before):
        crate_best_before_list()
    else:
        messagebox.showwarning(title='Warning', message=message_text)

def add_new_item_to_database():
    # Function to add a new item to the barcode database
    barcode = barcode_entry.get()
    product = product_entry.get()
    
    new_data = pd.DataFrame({'Barcode_ID': [barcode], 'Product_Name': [product]})
    updated_data = pd.concat([df, new_data], ignore_index=True)
    updated_data.to_csv('barcode_database.csv', index=False)
    product_entry.delete(0, END)
    barcode_entry.delete(0, END)

def show_inventory():
    # Function to display the best before inventory
    try:
        inventory = pd.read_csv('best_before.csv', encoding='UTF-8')

        # Create a new window for the inventory display
        inventory_window = Toplevel(window)
        inventory_window.title('Inventory')
        
        # Create a frame for the treeview widget
        tree_frame = Frame(inventory_window)
        tree_frame.pack(fill='both', expand=True)

        # Create a Treeview widget to display inventory data
        tree = ttk.Treeview(tree_frame)
        tree['columns'] = ('Product', 'Best Before')
        tree.column('#0', width=50, minwidth=25)
        tree.column('Product', width=100, minwidth=50)
        tree.column('Best Before', width=100, minwidth=50)
        tree.heading('#0', text='ID')
        tree.heading('Product', text='Product')
        tree.heading('Best Before', text='Best Before')
        
        # Add a scrollbar for vertical scrolling
        scroll = Scrollbar(tree_frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
    
        # Insert inventory data into the Treeview
        for index, items in inventory.iterrows():
            tree.insert('', 'end', text=(index + 1),
                        values=(items['Product_Name'],
                                items['Best_Before']))
        
        tree.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')
    
    except FileNotFoundError:
        messagebox.showwarning(title='Warning', message='Best Before list is not exist')
    

def distribution_graphic():
    try:
        inventory = pd.read_csv('best_before.csv', encoding='UTF-8')
            
        product_counts = inventory['Best_Before']
        expiration_counts = inventory['Product_Name']
        
        sns.scatterplot(y=expiration_counts, x=product_counts, marker='o', color='blue')
        
        plt.xlabel('Expiration Date')
        plt.ylabel('Products')
        plt.title('Distribution of Products According to Expiration Dates')
        
        plt.xticks(rotation=90, ha='right', fontsize=8)
        plt.yticks(fontsize=8)
        plt.tight_layout()
    
        plt.show()
        
    except FileNotFoundError:
        messagebox.showwarning(title='Warning', message='Best Before list is not exist')


def ask_to_gemini():
    try:
        # Read the inventory data from the CSV file
        inventory = pd.read_csv('best_before.csv', encoding='UTF-8')
        
        # Initialize an empty list to store soon-to-expire food items
        foods = []

        # Iterate over each row in the inventory
        for index, row in inventory.iterrows():
            # Parse the 'Best_Before' date string into a datetime object
            item_date = datetime.strptime(row['Best_Before'], "%Y-%m-%d")
            
            # Calculate the number of days until the item expires
            day_difference = (item_date - datetime.now()).days
            
            # If the item expires in less than 15 days, add it to the list of soon-to-expire items
            if day_difference < 15:
                foods.append(row['Product_Name'])

        # Create a new window for the Google Gemini AI chat
        ai_window = Toplevel(window)
        ai_window.title('Google Gemini AI')
        
        # Create a vertical scrollbar for the chat window
        scrollbar = Scrollbar(ai_window, orient='vertical')
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # Create a text box for displaying the chat messages
        text_box = Text(ai_window, height=50, width=100)
        text_box.pack(side=LEFT, fill=Y)

        # Configure the scrollbar to scroll the text box
        scrollbar.config(command=text_box.yview)

        # Configure Google Gemini AI with the API key
        genai.configure(api_key="API KEY HERE")
        
        # Set up the model for generating chat responses
        generation_config = {
            "temperature": 0.9,
            "top_p": 1,
            "top_k": 1,
            "max_output_tokens": 2048,
        }
        model = genai.GenerativeModel(model_name="gemini-1.0-pro", generation_config=generation_config)
        
        # Start a new conversation with the model
        convo = model.start_chat(history=[])
        
        # Create a message containing the list of soon-to-expire food items
        message = ', '.join([f'{item}' for item in foods])
        
        # Send a message to the model requesting recipes using the soon-to-expire food items
        convo.send_message(f'''You're a master chef model. I have {message}.
                           Can you create recipes for me from these products I have 
                           given, regardless of brands and product quantities?''')
        
        # Get the model's response and display it in the text box
        answer = convo.last.text
        text_box.insert(END, answer)

    except FileNotFoundError:
        # If the inventory file is not found, display a warning message
        messagebox.showwarning(title='Warning', message='Best Before list is not exist')
        

# ---------------------------- UI SETUP ------------------------------- #
window = Tk()
window.title("Best Before")
window.config(padx=50, pady=50)
window.geometry('500x400')

# Menu image
canvas = Canvas(window, width=400, height=200)
food_image = Image.open('food_image400x200.png')
food_image2 = ImageTk.PhotoImage(food_image)
canvas.create_image(200, 100, image=food_image2)
canvas.grid(row=0, column=0, columnspan=3)


# Barcode Entry Section settings
barcode_label = Label(window, text="Barcode:")
barcode_label.grid(row=1, column=0, sticky="W")
barcode_entry = Entry(window, width=35)
barcode_entry.grid(row=1, column=1, sticky="W")
barcode_entry.focus()

# Search Button settings
search_button = Button(window, text='Search', width=10, command=show_product)
search_button.grid(row=1, column=2, sticky="E")

# Product Section settings
product_label = Label(window, text="Product:")
product_label.grid(row=2, column=0, sticky="W")
product_entry = Entry(window, width=35)
product_entry.grid(row=2, column=1, sticky="W")
product_entry.focus()

# Add button settings
add_button = Button(window, text="Add",  width=10, command=add_new_item_to_database)
add_button.grid(row=2, column=2, sticky="E")

best_before_label = Label(window, text="Best Before:")
best_before_label.grid(row=3, column=0, sticky="W")
best_before_entry = Entry(window, width=35)
best_before_entry.grid(row=3, column=1, sticky="W")
best_before_entry.focus()

inventory_button = Button(window, text='Inventory', command=show_inventory)
inventory_button.grid(row=4, column=0)

analyse_button = Button(window, text='Analyse', command=distribution_graphic)
analyse_button.grid(row=4, column=1)

save_button = Button(window, text="Save",  width=10, command=check_date)
save_button.grid(row=3, column=2, sticky="E")


gpt_logo = Image.open("google_ai_logo_mini.png")
gpt_logo_image = ImageTk.PhotoImage(gpt_logo)
gpt_button = Button(window, image=gpt_logo_image, borderwidth=0, highlightthickness=0, command=ask_to_gemini)
gpt_button.grid(row=4, column=2)


window.grid_rowconfigure(4, minsize=20)
window.grid_rowconfigure(2, minsize=20)
window.mainloop()
