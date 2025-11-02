import re

def simple_symptom_checker(text):
    """Rule-based symptom to advice mapping."""
    text = text.lower()

    conditions = {
        "fever": "You might have a viral infection or flu. Stay hydrated, rest, and take paracetamol if needed.",
        "cough": "It sounds like a respiratory infection. Drink warm fluids and consider steam inhalation.",
        "cold": "You may be having a common cold. Rest, drink fluids, and use a saline nasal spray if congested.",
        "headache": "It could be due to dehydration or stress. Drink water and take a mild pain reliever if necessary.",
        "stomach": "This could indicate indigestion or food poisoning. Avoid heavy meals and stay hydrated.",
        "pain": "Pain can have many causes. Apply ice if it’s swelling, or rest if it’s muscular pain.",
        "body pain": "It may be due to viral fever or overexertion. Rest and hydrate well.",
        "rash": "Rashes may be allergic reactions. Avoid scratching and consult a dermatologist if it spreads.",
        "fracture": "It sounds serious. Avoid movement and visit an emergency clinic immediately.",
        "breathing": "Breathing difficulty can be serious. Please seek emergency medical help right away.",
        "vomit": "You may have a stomach infection. Drink electrolyte solutions and avoid solid food for a few hours.",
        "burn": "Apply cool water to the burn area and avoid applying toothpaste or oils. Visit a clinic if it’s severe."
    }

    # Match the most relevant condition
    for keyword, advice in conditions.items():
        if keyword in text:
            return {"condition": keyword, "advice": advice}

    return {
        "condition": "unknown condition",
        "advice": "Please describe your symptoms clearly, for example: 'I have a fever and cough.'"
    }
