import Foundation
import Combine

class Config: ObservableObject {
    static let shared = Config()

    // Keychain keys
    private enum Keys {
        static let openAIAPIKey = "openai_api_key"
        static let snowflakeAccount = "snowflake_account"
        static let snowflakeUser = "snowflake_user"
        static let snowflakePassword = "snowflake_password"
        static let snowflakeDatabase = "snowflake_database"
        static let snowflakeSchema = "snowflake_schema"
        static let snowflakeWarehouse = "snowflake_warehouse"
        static let snowflakeTable = "snowflake_table"
    }

    // MARK: - Constants
    static let openAIAPIURL = "https://api.openai.com/v1/audio/transcriptions"
    static let openAIModel = "whisper-1"

    // MARK: - Published Configuration
    @Published private(set) var isConfigured: Bool = false

    // MARK: - OpenAI Configuration
    var openAIAPIKey: String {
        // Try Keychain first, fallback to environment variable
        if let keychainValue = KeychainHelper.shared.retrieveString(forKey: Keys.openAIAPIKey), !keychainValue.isEmpty {
            return keychainValue
        }
        return ProcessInfo.processInfo.environment["OPENAI_API_KEY"] ?? ""
    }

    // MARK: - Snowflake Configuration
    var snowflakeAccount: String {
        if let keychainValue = KeychainHelper.shared.retrieveString(forKey: Keys.snowflakeAccount), !keychainValue.isEmpty {
            return keychainValue
        }
        return ProcessInfo.processInfo.environment["SNOWFLAKE_ACCOUNT"] ?? ""
    }

    var snowflakeUser: String {
        if let keychainValue = KeychainHelper.shared.retrieveString(forKey: Keys.snowflakeUser), !keychainValue.isEmpty {
            return keychainValue
        }
        return ProcessInfo.processInfo.environment["SNOWFLAKE_USER"] ?? ""
    }

    var snowflakePassword: String {
        if let keychainValue = KeychainHelper.shared.retrieveString(forKey: Keys.snowflakePassword), !keychainValue.isEmpty {
            return keychainValue
        }
        return ProcessInfo.processInfo.environment["SNOWFLAKE_PASSWORD"] ?? ""
    }

    var snowflakeDatabase: String {
        if let keychainValue = KeychainHelper.shared.retrieveString(forKey: Keys.snowflakeDatabase), !keychainValue.isEmpty {
            return keychainValue
        }
        return ProcessInfo.processInfo.environment["SNOWFLAKE_DATABASE"] ?? ""
    }

    var snowflakeSchema: String {
        if let keychainValue = KeychainHelper.shared.retrieveString(forKey: Keys.snowflakeSchema), !keychainValue.isEmpty {
            return keychainValue
        }
        return ProcessInfo.processInfo.environment["SNOWFLAKE_SCHEMA"] ?? ""
    }

    var snowflakeWarehouse: String {
        if let keychainValue = KeychainHelper.shared.retrieveString(forKey: Keys.snowflakeWarehouse), !keychainValue.isEmpty {
            return keychainValue
        }
        return ProcessInfo.processInfo.environment["SNOWFLAKE_WAREHOUSE"] ?? ""
    }

    var snowflakeTable: String {
        if let keychainValue = KeychainHelper.shared.retrieveString(forKey: Keys.snowflakeTable), !keychainValue.isEmpty {
            return keychainValue
        }
        return ProcessInfo.processInfo.environment["SNOWFLAKE_TABLE"] ?? "transcriptions"
    }

    private init() {
        updateConfigurationStatus()
    }

    // MARK: - Methods

    func reloadConfiguration() {
        updateConfigurationStatus()
    }

    private func updateConfigurationStatus() {
        isConfigured = !openAIAPIKey.isEmpty &&
                      !snowflakeAccount.isEmpty &&
                      !snowflakeUser.isEmpty &&
                      !snowflakePassword.isEmpty
    }
}
