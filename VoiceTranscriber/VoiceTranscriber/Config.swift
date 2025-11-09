import Foundation

struct Config {
    // MARK: - OpenAI Configuration
    static let openAIAPIKey = ProcessInfo.processInfo.environment["OPENAI_API_KEY"] ?? ""
    static let openAIAPIURL = "https://api.openai.com/v1/audio/transcriptions"
    static let openAIModel = "whisper-1"

    // MARK: - Snowflake Configuration
    static let snowflakeAccount = ProcessInfo.processInfo.environment["SNOWFLAKE_ACCOUNT"] ?? ""
    static let snowflakeUser = ProcessInfo.processInfo.environment["SNOWFLAKE_USER"] ?? ""
    static let snowflakePassword = ProcessInfo.processInfo.environment["SNOWFLAKE_PASSWORD"] ?? ""
    static let snowflakeDatabase = ProcessInfo.processInfo.environment["SNOWFLAKE_DATABASE"] ?? ""
    static let snowflakeSchema = ProcessInfo.processInfo.environment["SNOWFLAKE_SCHEMA"] ?? ""
    static let snowflakeWarehouse = ProcessInfo.processInfo.environment["SNOWFLAKE_WAREHOUSE"] ?? ""
    static let snowflakeTable = ProcessInfo.processInfo.environment["SNOWFLAKE_TABLE"] ?? "transcriptions"

    // Validation
    static var isConfigured: Bool {
        return !openAIAPIKey.isEmpty &&
               !snowflakeAccount.isEmpty &&
               !snowflakeUser.isEmpty &&
               !snowflakePassword.isEmpty
    }
}
