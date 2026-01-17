/**
 * Sample C++ module for testing the C++ parser.
 * Demonstrates classes, structs, namespaces, templates, and enums.
 */

#include <iostream>
#include <vector>
#include <string>

/**
 * Represents a 2D point.
 */
class Point {
public:
    /**
     * Construct a point with coordinates.
     */
    Point(int x, int y) : x_(x), y_(y) {}

    /** Get the X coordinate. */
    int getX() const { return x_; }

    /** Get the Y coordinate. */
    int getY() const { return y_; }

    /** Set the X coordinate. */
    void setX(int x) { x_ = x; }

    /** Set the Y coordinate. */
    void setY(int y) { y_ = y; }

private:
    int x_;
    int y_;
};

/**
 * A simple vector in 3D space.
 */
struct Vector3D {
    double x, y, z;

    /** Calculate the length of the vector. */
    double length() const {
        return std::sqrt(x*x + y*y + z*z);
    }
};

/**
 * Status codes for operations.
 */
enum class Status {
    Ok,
    Error,
    Pending
};

/**
 * Color enumeration.
 */
enum Color {
    Red = 0,
    Green = 1,
    Blue = 2
};

/**
 * Math utilities namespace.
 */
namespace math {
    /**
     * Add two numbers.
     */
    int add(int a, int b) {
        return a + b;
    }

    /**
     * Subtract two numbers.
     */
    int subtract(int a, int b) {
        return a - b;
    }

    /**
     * Calculator class for advanced operations.
     */
    class Calculator {
    public:
        /** Multiply two numbers. */
        int multiply(int a, int b) {
            return a * b;
        }

        /** Divide two numbers. */
        double divide(double a, double b) {
            return a / b;
        }
    };
}

/**
 * Nested namespace example.
 */
namespace utils {
    namespace string {
        /**
         * Convert string to uppercase.
         */
        std::string toUpper(const std::string& str) {
            std::string result = str;
            for (char& c : result) {
                c = std::toupper(c);
            }
            return result;
        }
    }
}

/**
 * A generic container template.
 */
template<typename T>
class Container {
public:
    /** Add an item to the container. */
    void add(const T& item) {
        items_.push_back(item);
    }

    /** Get the size of the container. */
    size_t size() const {
        return items_.size();
    }

    /** Get an item by index. */
    T& get(size_t index) {
        return items_[index];
    }

private:
    std::vector<T> items_;
};

/**
 * A template function for swapping values.
 */
template<typename T>
void swap(T& a, T& b) {
    T temp = a;
    a = b;
    b = temp;
}

/**
 * Create a point with default values.
 */
Point* createDefaultPoint() {
    return new Point(0, 0);
}

/**
 * Print a point to stdout.
 */
void printPoint(const Point& p) {
    std::cout << "Point(" << p.getX() << ", " << p.getY() << ")" << std::endl;
}

/**
 * Main entry point.
 */
int main(int argc, char* argv[]) {
    Point p(10, 20);
    printPoint(p);

    Container<int> container;
    container.add(1);
    container.add(2);

    return static_cast<int>(Status::Ok);
}
