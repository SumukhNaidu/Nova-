import pandas as pd
import matplotlib.pyplot as plt
import os
import matplotlib
matplotlib.use('Agg') # Use non-interactive backend for web servers

# Constants
DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'expenses.csv')
STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')
USERS_PATH = os.path.join(os.path.dirname(__file__), 'data', 'users.csv')

def load_data():
    if not os.path.exists(DATA_PATH):
        return pd.DataFrame(columns=['user_id', 'Date', 'Category', 'Amount', 'Description'])
    df = pd.read_csv(DATA_PATH)
    if 'user_id' not in df.columns:
        df['user_id'] = "1"
        df.to_csv(DATA_PATH, index=False)
    return df

def get_user_name(user_id):
    if not os.path.exists(USERS_PATH): return "Unknown Patient"
    users = pd.read_csv(USERS_PATH)
    u = users[users['user_id'].astype(str) == str(user_id)]
    if not u.empty: return u.iloc[0]['profile_name']
    return "Unknown Patient"

def add_expense_record(user_id, date, category, amount, description):
    df = load_data()
    new_expense = pd.DataFrame([{
        'user_id': str(user_id), 'Date': date, 'Category': category, 'Amount': amount, 'Description': description
    }])
    df = pd.concat([df, new_expense], ignore_index=True)
    df.to_csv(DATA_PATH, index=False)


def analyze_expenses(user_id):
    df = load_data()
    df = df[df['user_id'].astype(str) == str(user_id)]
    
    if df.empty:
        return {
            'total_expenses': 0,
            'invoices_pending': 0,
            'refunds_processed': 0,
            'highest_category': 'None',
            'highest_category_amount': 0,
            'category_distribution': {},
            'recent_expenses': []
        }
        
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
    total_expenses = df['Amount'].sum()
    
    # Calculate mock heuristic percentages for dynamic view
    invoices_pending = total_expenses * 0.15
    refunds_processed = total_expenses * 0.05
    
    category_group = df.groupby('Category')['Amount'].sum().sort_values(ascending=False)
    highest_category = category_group.index[0] if not category_group.empty else "None"
    highest_category_amount = category_group.iloc[0] if not category_group.empty else 0
    category_distribution = category_group.to_dict()
    recent_expenses = df.sort_values(by='Date', ascending=False).head(10).to_dict('records')
    
    return {
        'total_expenses': total_expenses,
        'invoices_pending': invoices_pending,
        'refunds_processed': refunds_processed,
        'highest_category': highest_category,
        'highest_category_amount': highest_category_amount,
        'category_distribution': category_distribution,
        'recent_expenses': recent_expenses
    }

def generate_charts(user_id):
    df = load_data()
    df = df[df['user_id'].astype(str) == str(user_id)]
    
    os.makedirs(STATIC_DIR, exist_ok=True)
    chart_filename = f'chart_category_{user_id}.png'
    chart_path = os.path.join(STATIC_DIR, chart_filename)
    
    if df.empty:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.text(0.5, 0.5, 'No Data Available', horizontalalignment='center', verticalalignment='center')
        ax.axis('off')
        plt.savefig(chart_path)
        plt.close()
        return chart_filename

    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
    category_group = df.groupby('Category')['Amount'].sum().sort_values(ascending=False)
    
    fig, ax = plt.subplots(figsize=(7, 7))
    colors = ['#005EB8', '#00A651', '#007B85', '#8EE8F3', '#D6E3FF', '#424752']
    wedges, texts, autotexts = ax.pie(category_group, autopct='%1.1f%%', startangle=90, colors=colors[:len(category_group)], textprops=dict(color="w"))
    ax.legend(wedges, category_group.index, title="Categories", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
    plt.title('Expense Distribution by Category', color='#191C1E', fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(chart_path, transparent=True, dpi=150)
    plt.close()
    
    return chart_filename

def chat_with_patient(user_id, prompt):
    df = load_data()
    df = df[df['user_id'].astype(str) == str(user_id)]
    
    prompt_lower = prompt.lower()
    
    if df.empty:
        return "You have no expenses logged yet! Once you add some expenses, I can help optimize your spending."
        
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
    total = df['Amount'].sum()
    
    if "total" in prompt_lower or "spent" in prompt_lower or "how much" in prompt_lower:
        return f"Based on your profile, you have spent a total of ₹{total:,.2f} so far. Is there a specific category you want to look at?"
        
    if "high" in prompt_lower or "most" in prompt_lower or "category" in prompt_lower or "categories" in prompt_lower or "expense" in prompt_lower:
        category_group = df.groupby('Category')['Amount'].sum().sort_values(ascending=False)
        highest = category_group.index[0] if not category_group.empty else "Nothing"
        amt = category_group.iloc[0] if not category_group.empty else 0
        return f"Your highest expense category is **{highest}** at ₹{amt:,.2f}. If this is unusually high, consider reviewing your insurance coverage for this sector."
        
    if "save" in prompt_lower or "reduce" in prompt_lower or "tip" in prompt_lower:
        category_group = df.groupby('Category')['Amount'].sum().sort_values(ascending=False)
        highest = category_group.index[0] if not category_group.empty else "None"
        if highest == "Pharmacy":
            return "Since Pharmacy is your highest expense, I recommend talking to your doctor about generic alternatives which can save up to 40%."
        return f"To save money on {highest}, make sure you are filing claims correctly. Many users miss out on deductible reimbursements."
        
    if "hello" in prompt_lower or "hi" in prompt_lower:
        return "Hello! I am your personal Health AI Advisor. You can ask me about your highest expenses, total budget, or ask for saving tips!"
        
    return "I'm your Health AI Assistant! You can ask me about how much you've spent, what your highest categories are, or for general advice on saving money on your current records."

if __name__ == "__main__":
    generate_charts()
