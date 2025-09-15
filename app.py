import os
# os.environ["TORCHINDUCTOR_DISABLED"] = "1"
# os.environ["ACCELERATE_DISABLE_INDUCTOR"] = "1"
# os.environ["TRITON_DISABLED"] = "1"
# os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
# os.environ["DISABLE_TORCH_DYNAMO"] = "1"  # <- new, to be extra sure
# import torch
# print(torch._dynamo.config)
# print("Torch backend:", os.environ.get("TORCHINDUCTOR_DISABLED"), "TorchInductor available:", hasattr(torch, "_inductor"))


import logging
from flask import Flask, render_template, send_from_directory, request, jsonify, redirect, url_for, flash
from flask_wtf import CSRFProtect
from database.db_model import db
from config import config
from application.container import get_container
from presentation.controllers import create_controllers


def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configure app
    app.secret_key = config.app.secret_key
    app.config['SQLALCHEMY_DATABASE_URI'] = config.database.url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config.database.echo
    app.config['MAX_CONTENT_LENGTH'] = config.app.max_content_length
    app.config['WTF_CSRF_TIME_LIMIT'] = config.app.csrf_time_limit
    
    # Initialize extensions
    db.init_app(app)
    csrf = CSRFProtect(app)
    
    # Initialize dependency container
    container = get_container(db)
    
    # Initialize controllers with dependency injection
    controllers = create_controllers()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO, 
        format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    
    # Register routes
    register_routes(app, csrf, controllers)
    
    # Register error handlers
    register_error_handlers(app)

    # print("Torch backend:", os.environ.get("TORCHINDUCTOR_DISABLED"), "TorchInductor available:", hasattr(torch, "_inductor"))

    
    return app


def register_routes(app, csrf, controllers):
    """Register all application routes"""
    
    # Authentication routes
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'GET':
            return render_template('login.html')
        result = controllers['auth'].login()

        print(f"Login JSON result: {result}")  # Debugging line to check login result
        return result


    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        if request.method == 'GET':
            return render_template('signup.html')
        
        result = controllers['auth'].signup()
        print(f"Signup result: {result}")  # Debugging line to check signup result
        print(f"Signup jsonify result: {jsonify(result)}")  # Debugging line to check signup result

        # Always return JSON if request is AJAX or expects JSON
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(result)
        else:
            if result.get('success'):
                return redirect(url_for('index'))
            else:
                flash(result.get('message', 'Sign up failed'), 'error')
                return redirect(url_for('signup'))
    
    @app.route('/logout')
    def logout():
        controllers['auth'].logout()
        return redirect(url_for('login'))
    
    @app.route('/about')
    def about():
        return render_template('about.html')
    
    
    @app.route('/forgot_password', methods=['GET', 'POST'])
    def forgot_password():
        if request.method == 'GET':
            return render_template('forgot_password.html')
        
        result = controllers['auth'].forgot_password()
        if result.get('success'):
            flash('Password reset link sent to your email.', 'success')
        else:
            flash(result.get('message', 'Failed to send reset link.'), 'error')
        return redirect(url_for('forgot_password'))
    
    @app.route('/home')
    def home():
        return render_template('home.html')
    
    @app.route('/chat')
    def chat_page():
        if not controllers['auth'].is_authenticated():
            return render_template('home.html')
        return render_template('chat.html')
    
    # Main routes
    @app.route('/')
    def index():
        if not controllers['auth'].is_authenticated():
            # return redirect(url_for('login'))
            return render_template('home.html')
        return render_template('chat.html')
        # return redirect(url_for('profile'))
    
    @app.route('/profile', methods=['GET', 'POST'])
    def profile():
        if not controllers['auth'].is_authenticated():
            return redirect(url_for('login'))
        
        if request.method == 'GET':
            result = controllers['user'].get_profile()
            if isinstance(result, tuple):
                return result
            return render_template('profile.html', user=result)
        
        result = controllers['user'].update_profile()
        if result.get('success'):
            flash('Profile updated successfully.', 'success')
        else:
            flash(result.get('error', 'Failed to update profile.'), 'error')
        return redirect(url_for('profile'))
    
    # Chat API routes
    @app.route("/get", methods=["GET", "POST"])
    def chat():
        if not controllers['auth'].is_authenticated():
            return jsonify({'response': 'Please log in to continue'})
        
        result = controllers['chat'].send_message()
        if isinstance(result, tuple):
            return result
        return jsonify(result)
    
    @app.route('/api/chat_sessions', methods=['GET'])
    def get_chat_sessions():
        if not controllers['auth'].is_authenticated():
            return jsonify({'error': 'Not authenticated'}), 401
        
        result = controllers['chat'].get_chat_sessions()
        if isinstance(result, tuple):
            return result
        return jsonify(result)
    
    # @app.route('/api/new_chat_session', methods=['POST'])
    # def new_chat_session():
    #     if not controllers['auth'].is_authenticated():
    #         return jsonify({'error': 'Not authenticated'}), 401
        
    #     # This would create a new session and optionally send a message
    #     data = request.get_json() if request.is_json else request.form
    #     msg = data.get("msg")
        
    #     # For now, redirect to the main chat endpoint
    #     return jsonify({'message': 'New session created'})

    @app.route('/api/new_chat_session', methods=['POST'])
    def new_chat_session():
        if not controllers['auth'].is_authenticated():
            return jsonify({'error': 'Not authenticated'}), 401

        user_id = controllers['auth'].get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401

        # Create a new session with a default title
        from datetime import datetime
        title = f"New Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        # student_id = user_id (assumption in current design)
        session = controllers['chat'].chat_service.create_chat_session(user_id, title)
        return jsonify({
            'session_id': session.session_id,
            'session_title': session.session_title,
            'created_at': session.created_at.strftime('%Y-%m-%d %H:%M') if session.created_at else ''
        })
    
    @app.route('/api/chat_sessions/<int:session_id>', methods=['PATCH'])
    def rename_chat_session(session_id):
        if not controllers['auth'].is_authenticated():
            return jsonify({'error': 'Not authenticated'}), 401
        
        result = controllers['chat'].rename_session(session_id)
        if isinstance(result, tuple):
            return result
        return jsonify(result)
    
    @app.route('/api/chat_sessions/<int:session_id>', methods=['DELETE'])
    def delete_chat_session(session_id):
        if not controllers['auth'].is_authenticated():
            return jsonify({'error': 'Not authenticated'}), 401
        
        result = controllers['chat'].delete_session(session_id)
        if isinstance(result, tuple):
            return result
        return jsonify(result)
    
    @app.route('/api/chat_messages/<int:session_id>', methods=['GET'])
    def get_chat_messages(session_id):
        if not controllers['auth'].is_authenticated():
            return jsonify({'error': 'Not authenticated'}), 401
        
        result = controllers['chat'].get_chat_messages(session_id)
        if isinstance(result, tuple):
            return result
        return jsonify(result)
    
    # Admin routes
    # @app.route('/admin', methods=['GET', 'POST'])
    # def admin_dashboard():
    #     if not controllers['auth'].is_admin():
    #         flash('You must be an admin to access this page.', 'danger')
    #         return redirect(url_for('login'))
        
    #     if request.method == 'GET':
    #         result = controllers['admin'].get_dashboard()
    #         if isinstance(result, tuple):
    #             return result
    #         return render_template('admin_dashboard.html', **result)
        
    #     # Handle file upload
    #     result = controllers['admin'].upload_training_file()
    #     if result.get('success'):
    #         flash('File uploaded successfully', 'success')
    #     else:
    #         flash(result.get('error', 'Failed to upload file.'), 'error')
    #     return redirect(url_for('admin_dashboard'))

    @app.route('/admin', methods=['GET', 'POST'])
    def admin_dashboard():
        if not controllers['auth'].is_admin():
            flash('You must be an admin to access this page.', 'danger')
            return redirect(url_for('login'))

        if request.method == 'POST':
            uploaded_file = request.files.get('training_file')
            if not uploaded_file or uploaded_file.filename == '':
                flash('No file selected.', 'danger')
                return redirect(url_for('admin_dashboard'))

            filename = uploaded_file.filename
            allowed_exts = ('.pdf', '.md')
            if not filename.lower().endswith(allowed_exts):
                flash('Invalid file type. Only PDF and MD allowed.', 'danger')
                return redirect(url_for('admin_dashboard'))

            save_dir = config.files.training_data_folder
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, filename)
            uploaded_file.save(save_path)
            flash('File uploaded successfully.', 'success')
            return redirect(url_for('admin_dashboard'))

        # GET
        result = controllers['admin'].get_dashboard()
        if isinstance(result, tuple):
            return result
        return render_template('admin_dashboard.html', **result)

    
    # @app.route('/admin/edit_student/<int:student_id>', methods=['POST'])
    # @csrf.exempt
    # def edit_student(student_id):
    #     if not controllers['auth'].is_admin():
    #         return jsonify({'error': 'Admin privileges required'}), 403
        
    #     result = controllers['admin'].manage_student(student_id)
    #     if isinstance(result, tuple):
    #         return result
    #     return jsonify(result)
    
    @app.route('/training_data/<path:filename>')
    def training_data(filename):
        if not controllers['auth'].is_admin():
            flash('You must be an admin to access this file.', 'danger')
            return redirect(url_for('login'))
        return send_from_directory(config.files.training_data_folder, filename)



    # @app.route('/admin/delete_student/<int:student_id>', methods=['POST'])
    # @csrf.exempt
    # def delete_student(student_id):
    #     if not controllers['auth'].is_admin():
    #         return jsonify({'error': 'Admin privileges required'}), 403
        
    #     result = controllers['admin'].manage_student(student_id)
    #     if isinstance(result, tuple):
    #         return result
    #     return jsonify(result)

    @app.route('/admin/edit_student/<int:student_id>', methods=['POST'])
    def edit_student(student_id):
        if not controllers['auth'].is_admin():
            return jsonify({'error': 'Admin privileges required'}), 403
        result = controllers['admin'].manage_student(student_id)
        if isinstance(result, tuple):
            return result
        flash('Student updated successfully.' if result.get('success') else result.get('error','Failed to update student.'), 
            'success' if result.get('success') else 'danger')
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/delete_student/<int:student_id>', methods=['POST'])
    def delete_student(student_id):
        if not controllers['auth'].is_admin():
            return jsonify({'error': 'Admin privileges required'}), 403
        result = controllers['admin'].manage_student(student_id)
        if isinstance(result, tuple):
            return result
        flash('Student deleted successfully.' if result.get('success') else result.get('error','Failed to delete student.'), 
            'success' if result.get('success') else 'danger')
        return redirect(url_for('admin_dashboard'))

    
    # Static file routes
    @app.route('/profile_pics/<filename>')
    def profile_pics(filename):
        return send_from_directory('profile_pics', filename)
    
    # @app.route('/training_data/<filename>')
    # def training_data(filename):
    #     if not controllers['auth'].is_admin():
    #         flash('You must be an admin to access this page.', 'danger')
    #         return redirect(url_for('login'))
    #     return send_from_directory('training_data', filename)


def register_error_handlers(app):
    """Register error handlers"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500


# Create app instance
app = create_app()

if __name__ == '__main__':
    # For development: create error templates if they don't exist
    if not os.path.exists('templates/404.html'):
        with open('templates/404.html', 'w') as f:
            f.write('<h1>404 Not Found</h1><p>The page you are looking for does not exist.</p>')
    if not os.path.exists('templates/500.html'):
        with open('templates/500.html', 'w') as f:
            f.write('<h1>500 Internal Server Error</h1><p>Something went wrong.</p>')
    
    app.run(debug=config.app.debug) 