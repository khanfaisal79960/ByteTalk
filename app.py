import os
from flask import Flask, render_template, request, redirect, url_for, flash, abort
import firebase_admin
from firebase_admin import credentials, firestore, auth
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from datetime import datetime
from dotenv import load_dotenv
import markdown

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_super_secret_key_change_this_in_production_98765')

FIREBASE_CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), 'firebase_credentials.json')

if not os.path.exists(FIREBASE_CREDENTIALS_PATH):
    print(f"Error: Firebase credentials file not found at {FIREBASE_CREDENTIALS_PATH}")
    print("Please download your service account key from Firebase Console and rename it to 'firebase_credentials.json'.")
    exit() # Exit the application if credentials are not found

try:
    cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Firebase initialized successfully!")
except Exception as e:
    print(f"Error initializing Firebase: {e}")
    exit()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Please log in to access this page. 🔑"
login_manager.login_message_category = "warning"

class User(UserMixin):
    """
    Represents a user for Flask-Login.
    The 'id' attribute is the Firebase User ID (UID).
    """
    def __init__(self, uid, email):
        self.id = uid
        self.email = email

    @staticmethod
    def get(user_id):
        """
        Loads a user from Firebase Authentication based on their UID.
        Used by Flask-Login's user_loader.
        """
        try:
            user_record = auth.get_user(user_id)
            return User(user_record.uid, user_record.email)
        except Exception:
            return None

@login_manager.user_loader
def load_user(user_id):
    """
    Callback function used by Flask-Login to reload the user object
    from the user ID stored in the session.
    """
    return User.get(user_id)


@app.route('/')
def index():
    """
    Displays the main blog homepage, listing all posts or search results.
    Includes logic for search functionality.
    """
    search_query = request.args.get('q') 

    posts_ref = db.collection('posts')

    all_posts_stream = posts_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).stream()
    
    posts = []

    for doc in all_posts_stream:
        post_data = doc.to_dict()

        if search_query:
            title_lower = post_data.get('title', '').lower()
            content_lower = post_data.get('content', '').lower()
            query_lower = search_query.lower()

            if query_lower not in title_lower and query_lower not in content_lower:
                continue 

        timestamp_display = 'Unknown Date'
        if post_data.get('timestamp'):
            if isinstance(post_data['timestamp'], datetime):
                timestamp_display = post_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            else:
                try:
                    timestamp_display = datetime.fromisoformat(post_data['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                except (ValueError, TypeError):
                    pass 

        snippet_content = post_data.get('content', 'No Content')
        if len(snippet_content) > 150:
            snippet_content = snippet_content[:150] + '...'
        
        posts.append({
            'id': doc.id,
            'title': post_data.get('title', 'No Title'),
            'content_snippet': snippet_content,
            'raw_content': post_data.get('content', 'No Content'), 
            'author': post_data.get('author', 'Anonymous'),
            'timestamp': timestamp_display,
            'is_author': current_user.is_authenticated and current_user.email == post_data.get('author')
        })
    
    if search_query and not posts:
        flash(f"No posts found matching '{search_query}'. Try a different vibe! 🔍", 'info')
    elif search_query:
        flash(f"Showing results for: '{search_query}'", 'info')

    return render_template('index.html', posts=posts, current_user=current_user, search_query=search_query)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    Handles user registration. Creates a new user in Firebase Authentication.
    """
    if current_user.is_authenticated:
        flash('You are already logged in. ✨', 'info')
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if not email or not password:
            flash('Email and password cannot be empty.', 'danger')
            return render_template('signup.html')
        
        if len(password) < 6: 
            flash('Password must be at least 6 characters long. 🔒', 'danger')
            return render_template('signup.html')

        try:
            user = auth.create_user(email=email, password=password)
            flash('Account created successfully! Please log in. 🔑', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            error_message = str(e)
            if 'EMAIL_EXISTS' in error_message:
                flash('This email is already registered. Try logging in or use a different email. 🤷‍♀️', 'danger')
            elif 'INVALID_EMAIL' in error_message:
                flash('The email address is not valid. 📧', 'danger')
            else:
                flash(f'Error creating account: {error_message}', 'danger')
            print(f"Error creating user: {e}")
            return render_template('signup.html')
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handles user login.
    IMPORTANT SECURITY NOTE: This simplified backend login does NOT securely verify passwords directly.
    In a production app, you would use Firebase Client SDK (JavaScript) on the frontend
    to handle signInWithEmailAndPassword, get an ID token, send that token to Flask,
    and then verify with auth.verify_id_token(id_token).
    This example only checks if a user with the provided email exists in Firebase Auth.
    """
    if current_user.is_authenticated:
        flash('You are already logged in. ✨', 'info')
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'] 

        if not email or not password:
            flash('Email and password cannot be empty.', 'danger')
            return render_template('login.html')

        try:
            user_record = auth.get_user_by_email(email)
            user = User(user_record.uid, user_record.email)
            login_user(user)
            flash('Logged in successfully! Welcome back. 🚀', 'success')
            return redirect(url_for('index'))

        except Exception as e:
            error_message = str(e)
            if 'user-not-found' in error_message or 'invalid-email' in error_message or 'No user record found' in error_message:
                flash('Invalid email or password.', 'danger')
            else:
                flash(f'An unexpected error occurred during login: {error_message}', 'danger')
            print(f"Login error: {e}")
            return render_template('login.html')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """
    Handles user logout.
    """
    logout_user() 
    flash('You have been logged out. See ya! 👋', 'info')
    return redirect(url_for('index'))

@app.route('/new_post', methods=['GET', 'POST'])
@login_required 
def new_post():
    """
    Handles displaying the new post form and submitting new posts to Firestore.
    """
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        author = current_user.email 

        if title and content:
            try:
                db.collection('posts').add({
                    'title': title,
                    'content': content, 
                    'author': author,
                    'timestamp': firestore.SERVER_TIMESTAMP 
                })
                flash('Your post has been published! ✨', 'success')
                return redirect(url_for('index'))
            except Exception as e:
                flash(f"Error saving post: {e}", 'danger')
                print(f"Error adding document: {e}")
                return "Error saving post.", 500 
        else:
            flash("Title and content cannot be empty. 🙄", 'warning')
            return render_template('new_post.html') 
    return render_template('new_post.html')

@app.route('/post/<post_id>')
def view_post(post_id):
    """
    Displays a single blog post by its ID.
    Renders Markdown content to HTML.
    """
    post_ref = db.collection('posts').document(post_id)
    post = post_ref.get()

    if post.exists:
        post_data = post.to_dict()
        timestamp_display = 'Unknown Date'
        if post_data.get('timestamp'):
            if isinstance(post_data['timestamp'], datetime):
                timestamp_display = post_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            else:
                try:
                    timestamp_display = datetime.fromisoformat(post_data['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                except (ValueError, TypeError):
                    pass
        
        html_content = markdown.markdown(post_data.get('content', ''))

        return render_template('view_post.html', post={
            'id': post.id,
            'title': post_data.get('title', 'No Title'),
            'content': html_content, # Pass the HTML rendered content
            'author': post_data.get('author', 'Anonymous'),
            'timestamp': timestamp_display,
            'raw_content': post_data.get('content', ''), 
            'is_author': current_user.is_authenticated and current_user.email == post_data.get('author')
        }, current_user=current_user)
    else:
        flash("Post not found. 🤷‍♀️", 'danger')
        return redirect(url_for('index'))

@app.route('/edit_post/<post_id>', methods=['GET', 'POST'])
@login_required 
def edit_post(post_id):
    """
    Handles editing an existing post.
    Allows only the author to edit their own post.
    """
    post_ref = db.collection('posts').document(post_id)
    post = post_ref.get()

    if not post.exists:
        flash('Post not found. 🤷‍♀️', 'danger')
        return redirect(url_for('index'))
    
    post_data = post.to_dict()

   
    if current_user.email != post_data.get('author'):
        flash("You can only edit your own posts! 🙅‍♂️", 'danger')
        return redirect(url_for('view_post', post_id=post_id)) 

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if title and content:
            try:
               
                post_ref.update({
                    'title': title,
                    'content': content,
                    'timestamp': firestore.SERVER_TIMESTAMP 
                })
                flash('Post updated successfully! ✨', 'success')
                return redirect(url_for('view_post', post_id=post_id))
            except Exception as e:
                flash(f"Error updating post: {e}", 'danger')
                print(f"Error updating document: {e}")
                return "Error updating post.", 500
        else:
            flash("Title and content cannot be empty. 🙄", 'warning')
            return render_template('edit_post.html', post={
                'id': post.id,
                'title': post_data.get('title', 'No Title'),
                'content': post_data.get('content', 'No Content')
            })
    

    return render_template('edit_post.html', post={
        'id': post.id,
        'title': post_data.get('title', 'No Title'),
        'content': post_data.get('content', 'No Content')
    })

@app.route('/delete_post/<post_id>', methods=['POST'])
@login_required 
def delete_post(post_id):
    """
    Handles deleting a post.
    Requires a POST request for security reasons.
    Allows only the author to delete their own post.
    """
    post_ref = db.collection('posts').document(post_id)
    post = post_ref.get()

    if not post.exists:
        flash('Post not found. 🤷‍♀️', 'danger')
        return redirect(url_for('index'))
    
    post_data = post.to_dict()

    if current_user.email != post_data.get('author'):
        flash("You can only delete your own posts! 🙅‍♂️", 'danger')
        return redirect(url_for('view_post', post_id=post_id)) 

    try:
        post_ref.delete() 
        flash('Post deleted successfully! 🗑️', 'info')
        return redirect(url_for('index'))
    except Exception as e:
        flash(f"Error deleting post: {e}", 'danger')
        print(f"Error deleting document: {e}")
        return "Error deleting post.", 500

# --- Error Handlers ---
@app.errorhandler(404)
def page_not_found(e):
    """
    Custom error handler for 404 Not Found errors.
    """
    return render_template('404.html'), 404 

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)