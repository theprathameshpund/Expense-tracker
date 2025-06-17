from flask import Flask, request, jsonify, render_template_string, redirect, url_for
from flask_cors import CORS
import uuid

app = Flask(__name__)
CORS(app)

# In-memory storage
expenses = []

@app.route("/", methods=["GET"])
def home():
    return render_template_string("""
        <h2>Add Expense</h2>
        <form method="POST" action="/add-expense">
            Name: <input type="text" name="name"><br><br>
            Amount: <input type="number" name="amount"><br><br>
            Paid By: <input type="text" name="paid_by"><br><br>
            <input type="submit" value="Submit">
        </form>
        <br><a href="/expenses-html">View All Expenses</a>
    """)

@app.route("/add-expense", methods=["POST"])
def add_expense():
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    if not all(k in data for k in ("name", "amount", "paid_by")):
        return jsonify({"error": "Missing required fields"}), 400

    expense = {
        "id": str(uuid.uuid4()),
        "name": data["name"],
        "amount": float(data["amount"]),
        "paid_by": data["paid_by"],
        "split_with": []  # initially empty
    }
    expenses.append(expense)

    if request.is_json:
        return jsonify(expense), 201
    else:
        return render_template_string("""
            <p><strong>Expense Added!</strong></p>
            <a href="/">Back to Form</a> | <a href="/expenses-html">View All Expenses</a>
        """)

@app.route("/expenses-html", methods=["GET"])
def view_expenses_html():
    if not expenses:
        return "<h3>No expenses recorded yet.</h3><a href='/'>Back</a>"

    html = "<h2>All Expenses</h2><ul>"
    for e in expenses:
        total_people = set(e['split_with'] + [e['paid_by']])
        num_people = len(total_people)
        share = round(e['amount'] / num_people, 2) if num_people else 0

        html += f"""
            <li>
                <strong>{e['name']}</strong>: ₹{e['amount']} paid by {e['paid_by']}<br>
                <em>Split With:</em><ul>
        """

        for person in total_people:
            html += f"<li>{person}: ₹{share}</li>"

        html += "</ul>"

        html += f"""
            <form action="/delete-expense/{e['id']}" method="POST" style="display:inline;">
                <button type="submit">Delete</button>
            </form>

            <form action="/split-expense/{e['id']}" method="POST" style="display:inline;">
                <input type="text" name="split_with" placeholder="Split with (comma-separated)">
                <button type="submit">Add Split</button>
            </form>
            </li><br>
        """
    html += "</ul><br><a href='/'>Add More</a>"
    return html

@app.route("/split-expense/<expense_id>", methods=["POST"])
def split_expense(expense_id):
    names = request.form.get("split_with", "")
    new_names = [n.strip() for n in names.split(",") if n.strip()]

    for expense in expenses:
        if expense["id"] == expense_id:
            existing = set(expense.get("split_with", []))
            expense["split_with"] = list(existing.union(new_names))
            break
    return redirect(url_for("view_expenses_html"))

@app.route("/delete-expense/<expense_id>", methods=["POST"])
def delete_expense_html(expense_id):
    global expenses
    expenses = [e for e in expenses if e["id"] != expense_id]
    return redirect(url_for("view_expenses_html"))

# Optional APIs (if needed for external systems)
@app.route("/view-expenses", methods=["GET"])
def view_expenses():
    return jsonify(expenses), 200

@app.route("/expenses/<expense_id>", methods=["DELETE"])
def delete_expense_api(expense_id):
    global expenses
    expenses = [e for e in expenses if e["id"] != expense_id]
    return jsonify({"message": "Expense deleted"}), 200

@app.route("/expenses/<expense_id>", methods=["PUT"])
def update_expense(expense_id):
    data = request.get_json()
    for expense in expenses:
        if expense["id"] == expense_id:
            expense["name"] = data.get("name", expense["name"])
            expense["amount"] = data.get("amount", expense["amount"])
            expense["paid_by"] = data.get("paid_by", expense["paid_by"])
            return jsonify(expense), 200
    return jsonify({"error": "Expense not found"}), 404

if __name__ == "__main__":
    app.run(debug=True)
