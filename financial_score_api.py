from fastapi import FastAPI, File, UploadFile
import pandas as pd
import json

app = FastAPI()

# Financial Scoring Model Function
def calculate_financial_score(row, data):
    savings_to_income = row['Savings'] / row['Income'] if row['Income'] != 0 else 0
    expenses_to_income = row['Monthly Expenses'] / row['Income'] if row['Income'] != 0 else 0
    loan_to_income = row['Loan Payments'] / row['Income'] if row['Income'] != 0 else 0
    cc_spending_to_income = row['Credit Card Spending'] / row['Income'] if row['Income'] != 0 else 0
    goals_met = row['Financial Goals Met (%)'] / 100

    # Penalize for high category spending
    total_spending = row['Amount']
    family_data = data[data['Family ID'] == row['Family ID']]
    travel_entertainment_spending = family_data.loc[(
        family_data['Category'] == 'Travel') | (family_data['Category'] == 'Entertainment'), 'Amount'].sum()

    category_penalty = 0
    if total_spending > 0 and travel_entertainment_spending / total_spending > 0.2:
        category_penalty = 5

    score = (
        (savings_to_income * 30) +
        ((1 - expenses_to_income) * 20) +
        ((1 - loan_to_income) * 20) +
        ((1 - cc_spending_to_income) * 20) +
        (goals_met * 10)
    ) * 100 / (30 + 20 + 20 + 20 + 10)

    score -= category_penalty
    return max(0, min(100, round(score, 2)))

# Recommendation function
def generate_recommendation(score):
    if score < 50:
        return "Focus on reducing discretionary spending and increasing savings."
    elif 50 <= score < 70:
        return "Maintain consistent savings; reduce high-interest loans."
    else:
        return "Good financial health! Continue current habits."

# Endpoint for processing family data
@app.post("/process/")
async def process_data(file: UploadFile = File(...)):
    # Get the file extension
    file_extension = file.filename.split('.')[-1].lower()

    # Read the file based on its extension
    if file_extension == 'xlsx':
        data = pd.read_excel(file.file)
    elif file_extension == 'csv':
        data = pd.read_csv(file.file)
    elif file_extension == 'json':
        content = await file.read()
        data = pd.read_json(content)
    else:
        return {"error": f"Unsupported file format: {file_extension}"}

    # Apply scoring to family-level data
    family_spending = data.groupby('Family ID').agg({
        'Amount': 'sum',
        'Income': 'mean',
        'Savings': 'mean',
        'Monthly Expenses': 'mean',
        'Loan Payments': 'mean',
        'Credit Card Spending': 'mean',
        'Financial Goals Met (%)': 'mean'
    }).reset_index()

    family_spending['Financial Score'] = family_spending.apply(
        lambda row: calculate_financial_score(row, data), axis=1)

    family_spending['Recommendation'] = family_spending['Financial Score'].apply(generate_recommendation)

    # Return processed data
    return family_spending.to_dict(orient='records')

# Entry point for running the FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
