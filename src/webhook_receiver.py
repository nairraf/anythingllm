from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        data = request.get_json()
        print("Received webhook data:", data)

        # You can trigger ingestion logic here
        # e.g., pull repo, filter files, upload to AnythingLLM

        return jsonify({"message": "Webhook received"}), 200
    return jsonify({"error": "Invalid request"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
