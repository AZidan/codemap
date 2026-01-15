import Foundation

/// Represents a user in the system.
struct User {
    let id: Int
    let name: String

    /// Gets the display name.
    func getDisplayName() -> String {
        return "\(name) (#\(id))"
    }

    /// Checks if user is valid.
    func isValid() -> Bool {
        return id > 0 && !name.isEmpty
    }
}

/// Service protocol for user operations.
protocol UserService {
    func getUser(id: Int) -> User?
    func createUser(name: String) -> User
    func deleteUser(id: Int) -> Bool
}

/// Status enumeration.
enum Status {
    case active
    case inactive
    case pending
}

/// Configuration class for the app.
class AppConfig {
    static let shared = AppConfig()
    let version = "1.0.0"

    private init() {}

    /// Gets the configuration string.
    func getConfigString() -> String {
        return "App v\(version)"
    }
}

/// Default implementation of UserService.
class DefaultUserService: UserService {
    private var users: [Int: User] = [:]

    /// Retrieves a user by ID.
    func getUser(id: Int) -> User? {
        return users[id]
    }

    /// Creates a new user with the given name.
    func createUser(name: String) -> User {
        let id = users.count + 1
        let user = User(id: id, name: name)
        users[id] = user
        return user
    }

    /// Deletes a user by ID.
    func deleteUser(id: Int) -> Bool {
        return users.removeValue(forKey: id) != nil
    }
}

/// Utility functions extension.
extension String {
    /// Converts string to title case.
    func toTitleCase() -> String {
        return self.components(separatedBy: " ")
            .map { $0.lowercased().capitalized }
            .joined(separator: " ")
    }
}

/// Top-level function for validation.
func validateEmail(_ email: String) -> Bool {
    return email.contains("@") && email.contains(".")
}
