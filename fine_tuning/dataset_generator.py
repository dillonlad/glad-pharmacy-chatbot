import random
import json

# Define the base context
context = """Our branch in Lowdham is open from 9am to 6pm on weekdays. 
The Lowdham branch is open 9am to 1pm on Saturdays. The Lowdham branch is closed on Sundays.
Our branch in Calverton is also open 9am to 6pm on weekdays. 
The Calverton branch is open 9am to 5pm on Saturdays. 
The Calverton branche is closed on Sundays. 
"""

contexts = [
    "The Lowdham branch operates from 9am to 6pm on weekdays, and from 9am to 1pm on Saturdays. Meanwhile, the Calverton branch is open from 9am to 6pm on weekdays and from 9am to 5pm on Saturdays. Both branches remain closed on Sundays. For bank holiday hours, refer here.",
    "You can visit our Lowdham branch between 9am and 6pm on weekdays and between 9am and 1pm on Saturdays. The Calverton branch is open 9am to 6pm on weekdays and 9am to 5pm on Saturdays. Both branches are closed Sundays. Check here for bank holiday opening times.",
    "Our Lowdham location opens from 9am to 6pm on weekdays and 9am to 1pm on Saturdays, while the Calverton location is open 9am to 6pm on weekdays and 9am to 5pm on Saturdays. Both branches are closed Sundays. Bank holiday hours are available here.",
    "Lowdham is open weekdays from 9am to 6pm and Saturdays from 9am to 1pm. Calverton has the same weekday hours but stays open later on Saturdays, until 5pm. Both branches are closed Sundays. Bank holiday hours can be found here.",
    "Weekday hours for the Lowdham branch are 9am to 6pm, with Saturday hours from 9am to 1pm. The Calverton branch is also open 9am to 6pm on weekdays but stays open until 5pm on Saturdays. Both branches are closed on Sundays. Details for bank holiday openings are available here.",
    "Visit Lowdham from 9am to 6pm during the week and from 9am to 1pm on Saturdays. Calverton follows the same weekday schedule but is open longer on Saturdays, until 5pm. Neither branch is open on Sundays. Bank holiday hours are listed here.",
    "Lowdham operates weekdays from 9am to 6pm and on Saturdays from 9am to 1pm. Calverton is open the same weekday hours but until 5pm on Saturdays. Both branches close Sundays. See here for bank holiday schedules.",
    "On weekdays, both branches—Lowdham and Calverton—are open from 9am to 6pm. Lowdham closes earlier on Saturdays, at 1pm, while Calverton closes at 5pm. Both branches are closed on Sundays. Check here for holiday hours.",
    "Our branches at Lowdham and Calverton are open from 9am to 6pm on weekdays. On Saturdays, Lowdham operates from 9am to 1pm, and Calverton operates from 9am to 5pm. Both branches remain closed on Sundays. Bank holiday details are here.",
    "Lowdham and Calverton have weekday hours of 9am to 6pm. Lowdham closes early on Saturdays, at 1pm, while Calverton stays open until 5pm. Both are closed on Sundays. Check here for details on bank holidays.",
    "You can visit Lowdham from 9am to 6pm on weekdays and 9am to 1pm on Saturdays. Calverton is open 9am to 6pm on weekdays and 9am to 5pm on Saturdays. Both are closed Sundays. See here for bank holiday hours.",
    "Our Lowdham branch is open on weekdays from 9am to 6pm and on Saturdays from 9am to 1pm. The Calverton branch operates 9am to 6pm during the week and 9am to 5pm on Saturdays. Both branches are closed on Sundays. Bank holiday hours can be found here.",
    "Lowdham opens weekdays from 9am to 6pm and Saturdays from 9am to 1pm. Calverton also operates 9am to 6pm on weekdays but stays open until 5pm on Saturdays. Both branches close Sundays. For bank holiday times, click here.",
    "Both Lowdham and Calverton branches open 9am to 6pm on weekdays. Lowdham is open 9am to 1pm on Saturdays, while Calverton operates until 5pm. Neither branch is open on Sundays. Bank holiday hours are provided here.",
    "The Lowdham branch operates weekdays from 9am to 6pm and Saturdays from 9am to 1pm. The Calverton branch is open weekdays from 9am to 6pm and Saturdays until 5pm. Both branches close on Sundays. Holiday hours can be checked here.",
    "Lowdham and Calverton are open weekdays 9am to 6pm. Saturdays, Lowdham closes at 1pm while Calverton stays open until 5pm. Both branches close Sundays. Bank holiday hours are available here.",
    "Lowdham operates from 9am to 6pm on weekdays and 9am to 1pm on Saturdays. Calverton shares the same weekday hours but closes at 5pm on Saturdays. Both branches close on Sundays. Holiday hours are available here.",
    "The Lowdham branch is open from 9am to 6pm Monday through Friday and from 9am to 1pm on Saturdays. Calverton operates 9am to 6pm on weekdays and 9am to 5pm on Saturdays. Both are closed Sundays. For holiday times, click here.",
    "You can visit our Lowdham branch from 9am to 6pm on weekdays and from 9am to 1pm on Saturdays. Calverton is open from 9am to 6pm on weekdays and 9am to 5pm on Saturdays. Both branches are closed Sundays. For bank holiday details, check here.",
    "Lowdham is open from 9am to 6pm Monday through Friday and from 9am to 1pm on Saturdays. Calverton shares the same weekday hours but stays open until 5pm on Saturdays. Both branches are closed Sundays. Holiday information is here.",
    "The weekday hours for Lowdham are 9am to 6pm, and on Saturdays, it is open from 9am to 1pm. Calverton has the same weekday hours but stays open until 5pm on Saturdays. Both branches remain closed on Sundays. Check here for bank holiday openings.",
    "On weekdays, both Lowdham and Calverton operate from 9am to 6pm. Lowdham is open Saturdays from 9am to 1pm, while Calverton stays open until 5pm. Both branches close Sundays. For bank holiday details, click here.",
    "Our Lowdham branch is open Monday to Friday from 9am to 6pm and on Saturdays from 9am to 1pm. The Calverton branch operates the same weekday hours but is open until 5pm on Saturdays. Both branches close on Sundays. For holiday hours, check here.",
    "Both Lowdham and Calverton branches are open weekdays from 9am to 6pm. Lowdham operates Saturdays from 9am to 1pm, while Calverton stays open until 5pm. Both locations close on Sundays. Bank holiday hours can be found here.",
    "During the week, Lowdham and Calverton are open from 9am to 6pm. On Saturdays, Lowdham closes earlier, at 1pm, while Calverton stays open until 5pm. Both branches are closed Sundays. Check here for holiday information.",
    "Lowdham is open Monday to Friday from 9am to 6pm and on Saturdays from 9am to 1pm. Calverton shares the same weekday hours but is open until 5pm on Saturdays. Both branches remain closed on Sundays. For bank holiday schedules, check here.",
    "The Lowdham branch is open from 9am to 6pm on weekdays, and from 9am to 1pm on Saturdays. Calverton follows the same weekday hours but operates until 5pm on Saturdays. Both branches are closed Sundays. For holiday hours, refer here.",
    "Our Lowdham branch operates Monday to Friday, 9am to 6pm, and Saturday from 9am to 1pm. Calverton runs the same weekday hours but remains open until 5pm on Saturdays. Both are closed on Sundays. Bank holiday details can be found here.",
    "Lowdham’s weekday hours are 9am to 6pm, with Saturday hours from 9am to 1pm. Calverton is open 9am to 6pm during the week and 9am to 5pm on Saturdays. Both branches are closed Sundays. For bank holiday times, click here.",
    "Weekdays, Lowdham is open from 9am to 6pm, and on Saturdays, it closes earlier, at 1pm. Calverton is open from 9am to 6pm on weekdays but until 5pm on Saturdays. Neither branch is open on Sundays. For more information, check here.",
    "Visit our Lowdham branch Monday through Friday from 9am to 6pm and Saturdays from 9am to 1pm. Calverton has the same weekday hours but remains open until 5pm on Saturdays. Both branches close on Sundays. Holiday hours are available here.",
    "On weekdays, Lowdham is open from 9am to 6pm and on Saturdays from 9am to 1pm. Calverton is open the same weekday hours but stays open until 5pm on Saturdays. Both locations close Sundays. Find bank holiday details here.",
    "Our Lowdham branch opens from 9am to 6pm during weekdays and from 9am to 1pm on Saturdays. Calverton operates the same hours on weekdays but stays open longer, until 5pm, on Saturdays. Both are closed Sundays. Holiday details are here.",
    "Both Lowdham and Calverton branches are open Monday to Friday, 9am to 6pm. On Saturdays, Lowdham closes at 1pm, while Calverton remains open until 5pm. Neither branch is open on Sundays. Bank holiday hours are available here.",
    "You can visit Lowdham Monday through Friday from 9am to 6pm and Saturdays from 9am to 1pm. Calverton has identical weekday hours but stays open until 5pm on Saturdays. Both branches are closed Sundays. See here for holiday hours.",
    "Our branches in Lowdham and Calverton operate from 9am to 6pm Monday to Friday. Lowdham closes at 1pm on Saturdays, while Calverton remains open until 5pm. Both locations are closed Sundays. Find more about holiday openings here.",
    "Lowdham opens weekdays at 9am and closes at 6pm, while Saturday hours are from 9am to 1pm. Calverton has the same weekday schedule but is open until 5pm on Saturdays. Both branches close on Sundays. Bank holiday hours are here.",
    "During the week, Lowdham and Calverton are open from 9am to 6pm. On Saturdays, Lowdham closes at 1pm, while Calverton stays open until 5pm. Both branches remain closed on Sundays. Bank holiday details are available here.",
    "The Lowdham branch has hours of 9am to 6pm Monday through Friday and 9am to 1pm on Saturdays. Calverton operates the same weekday schedule but stays open until 5pm on Saturdays. Both branches are closed Sundays. Holiday hours can be found here.",
    "Weekday hours for Lowdham are 9am to 6pm, and on Saturdays, it’s open 9am to 1pm. Calverton shares the same weekday hours but closes at 5pm on Saturdays. Both locations are closed on Sundays. For bank holiday times, refer here.",
    "Our Lowdham branch is open Monday to Friday, 9am to 6pm, and on Saturdays from 9am to 1pm. Calverton has the same weekday hours but operates until 5pm on Saturdays. Both branches remain closed on Sundays. For holiday schedules, click here.",
    "Lowdham is open 9am to 6pm on weekdays and 9am to 1pm on Saturdays. Calverton operates with the same weekday hours but stays open until 5pm on Saturdays. Both branches close Sundays. Check here for bank holiday information.",
    "Our Lowdham and Calverton branches are open Monday to Friday, 9am to 6pm. On Saturdays, Lowdham closes earlier, at 1pm, while Calverton stays open until 5pm. Both branches are closed on Sundays. Bank holiday details are here.",
    "Both branches—Lowdham and Calverton—have weekday hours of 9am to 6pm. Lowdham is open from 9am to 1pm on Saturdays, while Calverton is open until 5pm. Neither branch operates on Sundays. For holiday openings, click here.",
    "Lowdham’s opening hours are 9am to 6pm during the week and 9am to 1pm on Saturdays. Calverton shares the same weekday hours but remains open until 5pm on Saturdays. Both locations close Sundays. Holiday information is here.",
    "On weekdays, Lowdham and Calverton branches are open from 9am to 6pm. Lowdham operates Saturdays from 9am to 1pm, while Calverton stays open until 5pm. Both branches are closed Sundays. For holiday hours, click here.",
    "Our Lowdham branch is open 9am to 6pm Monday through Friday and from 9am to 1pm on Saturdays. Calverton follows the same weekday schedule but stays open until 5pm on Saturdays. Both branches are closed Sundays. Find more details here.",
    "Both branches operate from 9am to 6pm Monday through Friday. Lowdham is open 9am to 1pm on Saturdays, while Calverton stays open until 5pm. Neither branch is open on Sundays. See here for holiday information.",
    "Lowdham operates Monday to Friday, 9am to 6pm, and Saturdays from 9am to 1pm. Calverton follows the same weekday schedule but is open until 5pm on Saturdays. Both branches remain closed Sundays. For holiday details, click here.",
    "Our Lowdham branch is open weekdays from 9am to 6pm and Saturdays from 9am to 1pm. Calverton follows the same weekday hours but stays open until 5pm on Saturdays. Both branches close Sundays. Holiday hours can be checked here."
]


# Define some base question templates for variations
question_templates = [
    "What are your opening hours?",
    "Can you tell me the opening hours for your branches?",
    "When do your branches open and close?",
    "What time do you open during the week?",
    "What are your working hours on Saturdays?",
    "Are your branches open on Sundays?",
    "Can you tell me the hours for the Lowdham branch?",
    "What time does Calverton open and close?",
    "Could you share your weekday hours?",
    "When are your branches open on weekends?",
    "Do you open on Sundays?",
    "What’s the closing time for the Calverton branch?",
    "When can I visit the Lowdham branch during the week?",
    "Can you tell me the weekend hours for Lowdham?",
    "Are you open all day on Saturdays?",
    "What are your weekday operating hours?",
    "How late are you open on Saturdays in Calverton?",
    "When is the Lowdham branch open on Saturdays?",
    "Is your Lowdham branch open past 6pm?",
    "What are your operating hours for both branches?",
    "When can I visit Lowdham or Calverton?",
]

# Create 500 variations by randomizing templates and details
dataset = []
for i in range(500):
    # Randomly choose a template and optionally tweak it
    question = random.choice(question_templates)
    if random.random() > 0.5:
        # Add variations to the question (e.g., rephrasing or adding "please")
        question = f"Could you please tell me, {question.lower()}"

    rand_index = random.randint(0, 49)
    _context = contexts[rand_index]
    
    answer = context
    answer_start = 0

    # Add the example to the dataset
    dataset.append({
        "context": _context,
        "question": question,
        "answer_start": answer_start,
        "answer": answer,
    })

# Save the dataset to a JSON file
file_path = "pharmacy_opening_hours_500_variations_varied_context.json"
with open(file_path, "w") as f:
    json.dump(dataset, f, indent=4)

print(f"Dataset saved to {file_path}")
