from app import app

# For Debug Only:
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9999, debug=True, threaded=True)
