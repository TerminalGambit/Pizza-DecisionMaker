from flask import Flask, render_template, request, redirect, url_for, session
import json

app = Flask(__name__)
app.secret_key = "pizza-secret"

# Load pizza data
def load_pizzas():
    with open("pizzas.json", "r") as file:
        return json.load(file)

# Save pizzas back to JSON
def save_pizzas(pizzas):
    with open("pizzas.json", "w") as file:
        json.dump(pizzas, file, indent=4)

# Decision tree structure for questions
questions = {
    "vegan": {
        "question": "Are you vegan?",
        "if_yes": "allergies",
        "if_no": "vegetarian"
    },
    "vegetarian": {
        "question": "Are you vegetarian?",
        "if_yes": "mozzarella",
        "if_no": "cured_meats"
    },
    "mozzarella": {
        "question": "Do you want mozzarella?",
        "if_yes": "creamy_cheeses",
        "if_no": "creamy_cheeses"
    },
    "creamy_cheeses": {
        "question": "Do you prefer creamy cheeses (e.g., ricotta, brie)?",
        "if_yes": "allergies",
        "if_no": "allergies"
    },
    "cured_meats": {
        "question": "Would you like cured meats (e.g., ham, salami)?",
        "if_yes": "seafood",
        "if_no": "seafood"
    },
    "seafood": {
        "question": "Are you okay with seafood (e.g., tuna, anchovies)?",
        "if_yes": "allergies",
        "if_no": "allergies"
    },
    "allergies": {
        "question": "Do you have any allergies?",
        "if_yes": "gluten",
        "if_no": "ingredients"
    },
    "gluten": {
        "question": "Are you allergic to gluten?",
        "if_yes": "dairy",
        "if_no": "dairy"
    },
    "dairy": {
        "question": "Are you allergic to dairy?",
        "if_yes": "seafood_allergy",
        "if_no": "seafood_allergy"
    },
    "seafood_allergy": {
        "question": "Are you allergic to seafood?",
        "if_yes": "ingredients",
        "if_no": "ingredients"
    },
    "ingredients": {
        "question": "Do you want tomato sauce?",
        "if_yes": "vegetables",
        "if_no": "vegetables"
    },
    "vegetables": {
        "question": "Do you like fresh vegetables (e.g., eggplants, zucchini, peppers)?",
        "if_yes": "spicy",
        "if_no": "spicy"
    },
    "spicy": {
        "question": "Do you enjoy spicy flavors?",
        "if_yes": None,
        "if_no": None
    }
}

@app.route("/", methods=["GET"])
def welcome():
    """Render the welcome screen."""
    session.clear()
    session["preferences"] = {}
    session["started"] = True
    return render_template("welcome.html")

@app.route("/question/<question_key>", methods=["GET", "POST"])
def question(question_key):
    """Handle dynamic question display."""
    if not session.get("started"):
        return redirect(url_for("welcome"))

    question_node = questions.get(question_key)
    if not question_node:
        return redirect(url_for("results"))

    if request.method == "POST":
        answer = request.form.get("answer")
        session[question_node["question"]] = answer == "yes"

        # Update preferences dynamically
        key_map = {
            "mozzarella": "Mozzarella",
            "cured_meats": "Meats",
            "seafood": "Fish",
            "spicy": "Spicy salami"
        }
        if question_key in key_map:
            session["preferences"][key_map[question_key]] = answer == "yes"

        next_question_key = question_node.get("if_yes") if answer == "yes" else question_node.get("if_no")
        if next_question_key:
            return redirect(url_for("question", question_key=next_question_key))
        else:
            return redirect(url_for("results"))

    return render_template("question.html", question=question_node["question"])

@app.route("/results")
def results():
    """Generate results based on user preferences."""
    preferences = session.get("preferences", {})
    pizzas = load_pizzas()

    # Match pizzas with preferences
    scored_pizzas = match_pizzas_with_preferences(pizzas, preferences)

    # Debugging: Log final scored pizzas
    for pizza in scored_pizzas:
        print(f"Pizza: {pizza['name']}, Score: {pizza['score']}")

    return render_template("results.html", pizzas=scored_pizzas[:3])

def match_pizzas_with_preferences(pizzas, preferences):
    """Filter and rank pizzas based on user preferences."""
    pizzas_copy = [dict(pizza) for pizza in pizzas]  # Create a temporary copy
    for pizza in pizzas_copy:
        ingredients_list = pizza["ingredients"]
        score = 0

        for ingredient, wants in preferences.items():
            has_ingredient = any(ingredient.lower() in ing.lower() for ing in ingredients_list)
            if wants and has_ingredient:
                score += 1  # Reward for matching preference
            elif not wants and has_ingredient:
                score -= 0.5  # Penalize for conflicting preference

        pizza["score"] = score

    # Sort pizzas by score (highest first)
    pizzas_copy.sort(key=lambda x: x["score"], reverse=True)
    return pizzas_copy

if __name__ == "__main__":
    app.run(debug=True)