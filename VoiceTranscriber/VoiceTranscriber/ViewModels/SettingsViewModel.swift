import Foundation
import SwiftUI

class SettingsViewModel: ObservableObject {
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

    // Published properties for UI binding
    @Published var openAIAPIKey: String = ""
    @Published var snowflakeAccount: String = ""
    @Published var snowflakeUser: String = ""
    @Published var snowflakePassword: String = ""
    @Published var snowflakeDatabase: String = ""
    @Published var snowflakeSchema: String = ""
    @Published var snowflakeWarehouse: String = ""
    @Published var snowflakeTable: String = "transcriptions"

    @Published var showingSaveConfirmation = false
    @Published var saveError: String?
    @Published var showingError = false

    init() {
        loadSettings()
    }

    // MARK: - Load Settings

    func loadSettings() {
        openAIAPIKey = KeychainHelper.shared.retrieveString(forKey: Keys.openAIAPIKey) ?? ""
        snowflakeAccount = KeychainHelper.shared.retrieveString(forKey: Keys.snowflakeAccount) ?? ""
        snowflakeUser = KeychainHelper.shared.retrieveString(forKey: Keys.snowflakeUser) ?? ""
        snowflakePassword = KeychainHelper.shared.retrieveString(forKey: Keys.snowflakePassword) ?? ""
        snowflakeDatabase = KeychainHelper.shared.retrieveString(forKey: Keys.snowflakeDatabase) ?? ""
        snowflakeSchema = KeychainHelper.shared.retrieveString(forKey: Keys.snowflakeSchema) ?? ""
        snowflakeWarehouse = KeychainHelper.shared.retrieveString(forKey: Keys.snowflakeWarehouse) ?? ""
        snowflakeTable = KeychainHelper.shared.retrieveString(forKey: Keys.snowflakeTable) ?? "transcriptions"
    }

    // MARK: - Save Settings

    func saveSettings() {
        do {
            // Save all settings to keychain
            try KeychainHelper.shared.save(openAIAPIKey, forKey: Keys.openAIAPIKey)
            try KeychainHelper.shared.save(snowflakeAccount, forKey: Keys.snowflakeAccount)
            try KeychainHelper.shared.save(snowflakeUser, forKey: Keys.snowflakeUser)
            try KeychainHelper.shared.save(snowflakePassword, forKey: Keys.snowflakePassword)
            try KeychainHelper.shared.save(snowflakeDatabase, forKey: Keys.snowflakeDatabase)
            try KeychainHelper.shared.save(snowflakeSchema, forKey: Keys.snowflakeSchema)
            try KeychainHelper.shared.save(snowflakeWarehouse, forKey: Keys.snowflakeWarehouse)
            try KeychainHelper.shared.save(snowflakeTable.isEmpty ? "transcriptions" : snowflakeTable, forKey: Keys.snowflakeTable)

            // Update Config singleton
            Config.shared.reloadConfiguration()

            showingSaveConfirmation = true
        } catch {
            saveError = "Failed to save settings: \(error.localizedDescription)"
            showingError = true
        }
    }

    // MARK: - Clear Settings

    func clearSettings() {
        do {
            try KeychainHelper.shared.delete(forKey: Keys.openAIAPIKey)
            try KeychainHelper.shared.delete(forKey: Keys.snowflakeAccount)
            try KeychainHelper.shared.delete(forKey: Keys.snowflakeUser)
            try KeychainHelper.shared.delete(forKey: Keys.snowflakePassword)
            try KeychainHelper.shared.delete(forKey: Keys.snowflakeDatabase)
            try KeychainHelper.shared.delete(forKey: Keys.snowflakeSchema)
            try KeychainHelper.shared.delete(forKey: Keys.snowflakeWarehouse)
            try KeychainHelper.shared.delete(forKey: Keys.snowflakeTable)

            loadSettings()
            Config.shared.reloadConfiguration()
        } catch {
            saveError = "Failed to clear settings: \(error.localizedDescription)"
            showingError = true
        }
    }

    // MARK: - Validation

    var isOpenAIConfigured: Bool {
        !openAIAPIKey.isEmpty
    }

    var isSnowflakeConfigured: Bool {
        !snowflakeAccount.isEmpty &&
        !snowflakeUser.isEmpty &&
        !snowflakePassword.isEmpty &&
        !snowflakeDatabase.isEmpty &&
        !snowflakeSchema.isEmpty &&
        !snowflakeWarehouse.isEmpty
    }

    var isFullyConfigured: Bool {
        isOpenAIConfigured && isSnowflakeConfigured
    }
}
