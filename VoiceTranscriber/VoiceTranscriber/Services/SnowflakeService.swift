import Foundation

class SnowflakeService {
    static let shared = SnowflakeService()

    private init() {}

    func uploadTranscription(recording: Recording) async throws {
        guard !Config.shared.snowflakeAccount.isEmpty,
              !Config.shared.snowflakeUser.isEmpty,
              !Config.shared.snowflakePassword.isEmpty else {
            throw SnowflakeError.missingConfiguration
        }

        guard let transcription = recording.transcription else {
            throw SnowflakeError.missingTranscription
        }

        // Snowflake SQL API endpoint
        let urlString = "https://\(Config.shared.snowflakeAccount).snowflakecomputing.com/api/v2/statements"
        guard let url = URL(string: urlString) else {
            throw SnowflakeError.invalidURL
        }

        // Create authentication header
        let credentials = "\(Config.shared.snowflakeUser):\(Config.shared.snowflakePassword)"
        guard let credentialsData = credentials.data(using: .utf8) else {
            throw SnowflakeError.authenticationFailed
        }
        let base64Credentials = credentialsData.base64EncodedString()

        // Prepare SQL statement
        let table = Config.shared.snowflakeTable.isEmpty ? "transcriptions" : Config.shared.snowflakeTable
        let database = Config.shared.snowflakeDatabase
        let schema = Config.shared.snowflakeSchema
        let warehouse = Config.shared.snowflakeWarehouse

        // Escape single quotes in transcription
        let escapedTranscription = transcription.replacingOccurrences(of: "'", with: "''")

        let sqlStatement = """
        INSERT INTO \(database).\(schema).\(table)
        (id, filename, recording_date, transcription, duration, uploaded_at)
        VALUES (
            '\(recording.id.uuidString)',
            '\(recording.filename)',
            '\(ISO8601DateFormatter().string(from: recording.date))',
            '\(escapedTranscription)',
            \(recording.duration),
            CURRENT_TIMESTAMP()
        )
        """

        // Create request body
        let requestBody: [String: Any] = [
            "statement": sqlStatement,
            "timeout": 60,
            "database": database,
            "schema": schema,
            "warehouse": warehouse
        ]

        guard let jsonData = try? JSONSerialization.data(withJSONObject: requestBody) else {
            throw SnowflakeError.invalidRequest
        }

        // Create request
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Basic \(base64Credentials)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.httpBody = jsonData

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw SnowflakeError.invalidResponse
        }

        guard httpResponse.statusCode == 200 else {
            if let errorMessage = String(data: data, encoding: .utf8) {
                print("Snowflake API Error: \(errorMessage)")
            }
            throw SnowflakeError.apiError(statusCode: httpResponse.statusCode)
        }

        // Check if the statement was successful
        if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
           let code = json["code"] as? String,
           code != "090001" { // 090001 is success code
            throw SnowflakeError.queryFailed
        }
    }

    func createTableIfNeeded() async throws {
        guard !Config.shared.snowflakeAccount.isEmpty,
              !Config.shared.snowflakeUser.isEmpty,
              !Config.shared.snowflakePassword.isEmpty else {
            throw SnowflakeError.missingConfiguration
        }

        let urlString = "https://\(Config.shared.snowflakeAccount).snowflakecomputing.com/api/v2/statements"
        guard let url = URL(string: urlString) else {
            throw SnowflakeError.invalidURL
        }

        let credentials = "\(Config.shared.snowflakeUser):\(Config.shared.snowflakePassword)"
        guard let credentialsData = credentials.data(using: .utf8) else {
            throw SnowflakeError.authenticationFailed
        }
        let base64Credentials = credentialsData.base64EncodedString()

        let table = Config.shared.snowflakeTable.isEmpty ? "transcriptions" : Config.shared.snowflakeTable
        let database = Config.shared.snowflakeDatabase
        let schema = Config.shared.snowflakeSchema
        let warehouse = Config.shared.snowflakeWarehouse

        let sqlStatement = """
        CREATE TABLE IF NOT EXISTS \(database).\(schema).\(table) (
            id VARCHAR(255) PRIMARY KEY,
            filename VARCHAR(500),
            recording_date TIMESTAMP,
            transcription TEXT,
            duration FLOAT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
        )
        """

        let requestBody: [String: Any] = [
            "statement": sqlStatement,
            "timeout": 60,
            "database": database,
            "schema": schema,
            "warehouse": warehouse
        ]

        guard let jsonData = try? JSONSerialization.data(withJSONObject: requestBody) else {
            throw SnowflakeError.invalidRequest
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Basic \(base64Credentials)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.httpBody = jsonData

        let (_, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw SnowflakeError.queryFailed
        }
    }

    enum SnowflakeError: LocalizedError {
        case missingConfiguration
        case missingTranscription
        case invalidURL
        case authenticationFailed
        case invalidRequest
        case invalidResponse
        case apiError(statusCode: Int)
        case queryFailed

        var errorDescription: String? {
            switch self {
            case .missingConfiguration:
                return "Snowflake configuration is missing. Please configure your Snowflake credentials."
            case .missingTranscription:
                return "No transcription available to upload."
            case .invalidURL:
                return "Invalid Snowflake URL."
            case .authenticationFailed:
                return "Snowflake authentication failed."
            case .invalidRequest:
                return "Invalid request to Snowflake."
            case .invalidResponse:
                return "Invalid response from Snowflake."
            case .apiError(let statusCode):
                return "Snowflake API error with status code: \(statusCode)"
            case .queryFailed:
                return "Snowflake query failed."
            }
        }
    }
}
