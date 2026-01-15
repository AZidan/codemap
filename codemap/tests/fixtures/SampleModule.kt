package com.example.sample

/**
 * Represents a user in the system.
 */
data class User(
    val id: Int,
    val name: String
) {
    /**
     * Gets the display name.
     */
    fun getDisplayName(): String {
        return "$name (#$id)"
    }

    /**
     * Checks if user is valid.
     */
    fun isValid(): Boolean {
        return id > 0 && name.isNotEmpty()
    }
}

/**
 * Service interface for user operations.
 */
interface UserService {
    fun getUser(id: Int): User?
    fun createUser(name: String): User
    fun deleteUser(id: Int): Boolean
}

/**
 * Status enumeration.
 */
enum class Status {
    ACTIVE,
    INACTIVE,
    PENDING
}

/**
 * Singleton configuration object.
 */
object AppConfig {
    val version = "1.0.0"

    /**
     * Gets the configuration string.
     */
    fun getConfigString(): String {
        return "App v$version"
    }
}

/**
 * Default implementation of UserService.
 */
class DefaultUserService : UserService {
    private val users = mutableMapOf<Int, User>()

    /**
     * Retrieves a user by ID.
     */
    override fun getUser(id: Int): User? {
        return users[id]
    }

    /**
     * Creates a new user with the given name.
     */
    override fun createUser(name: String): User {
        val id = users.size + 1
        val user = User(id, name)
        users[id] = user
        return user
    }

    /**
     * Deletes a user by ID.
     */
    override fun deleteUser(id: Int): Boolean {
        return users.remove(id) != null
    }
}

/**
 * Utility functions for string operations.
 */
fun String.toTitleCase(): String {
    return split(" ").joinToString(" ") { word ->
        word.lowercase().replaceFirstChar { it.uppercase() }
    }
}

/**
 * Top-level function for validation.
 */
fun validateEmail(email: String): Boolean {
    return email.contains("@") && email.contains(".")
}
