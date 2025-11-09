import Foundation

class OpenAIService {
    static let shared = OpenAIService()

    private init() {}

    func transcribeAudio(fileURL: URL) async throws -> String {
        guard !Config.shared.openAIAPIKey.isEmpty else {
            throw TranscriptionError.missingAPIKey
        }

        let boundary = UUID().uuidString
        var request = URLRequest(url: URL(string: Config.openAIAPIURL)!)
        request.httpMethod = "POST"
        request.setValue("Bearer \(Config.shared.openAIAPIKey)", forHTTPHeaderField: "Authorization")
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        let httpBody = createMultipartBody(
            fileURL: fileURL,
            boundary: boundary,
            model: Config.openAIModel
        )
        request.httpBody = httpBody

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw TranscriptionError.invalidResponse
        }

        guard httpResponse.statusCode == 200 else {
            if let errorMessage = String(data: data, encoding: .utf8) {
                print("OpenAI API Error: \(errorMessage)")
            }
            throw TranscriptionError.apiError(statusCode: httpResponse.statusCode)
        }

        guard let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let text = json["text"] as? String else {
            throw TranscriptionError.invalidResponse
        }

        return text
    }

    private func createMultipartBody(fileURL: URL, boundary: String, model: String) -> Data {
        var body = Data()
        let lineBreak = "\r\n"

        // Add model parameter
        body.append("--\(boundary)\(lineBreak)")
        body.append("Content-Disposition: form-data; name=\"model\"\(lineBreak)\(lineBreak)")
        body.append("\(model)\(lineBreak)")

        // Add file data
        body.append("--\(boundary)\(lineBreak)")
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(fileURL.lastPathComponent)\"\(lineBreak)")
        body.append("Content-Type: audio/m4a\(lineBreak)\(lineBreak)")

        if let fileData = try? Data(contentsOf: fileURL) {
            body.append(fileData)
        }

        body.append(lineBreak)
        body.append("--\(boundary)--\(lineBreak)")

        return body
    }

    enum TranscriptionError: LocalizedError {
        case missingAPIKey
        case invalidResponse
        case apiError(statusCode: Int)

        var errorDescription: String? {
            switch self {
            case .missingAPIKey:
                return "OpenAI API key is missing. Please configure OPENAI_API_KEY."
            case .invalidResponse:
                return "Invalid response from OpenAI API."
            case .apiError(let statusCode):
                return "OpenAI API error with status code: \(statusCode)"
            }
        }
    }
}

extension Data {
    mutating func append(_ string: String) {
        if let data = string.data(using: .utf8) {
            append(data)
        }
    }
}
