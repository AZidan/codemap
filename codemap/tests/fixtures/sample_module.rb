# Sample Ruby module for CodeMap testing
# Includes various Ruby and Rails patterns

# Top-level module with nested classes
module Authentication
  # Constants
  DEFAULT_TIMEOUT = 3600

  # Module-level class method
  def self.configure
    yield configuration if block_given?
  end

  # Configuration class
  class Configuration
    attr_accessor :secret_key, :timeout

    def initialize
      @timeout = DEFAULT_TIMEOUT
    end
  end

  # Concern-like module for Rails
  module Authenticatable
    # Called when module is included
    def self.included(base)
      base.extend(ClassMethods)
    end

    # Instance methods
    def authenticate!
      redirect_to login_path unless current_user
    end

    def current_user
      @current_user ||= User.find(session[:user_id])
    end

    # Class methods module
    module ClassMethods
      def authentication_required
        before_action :authenticate!
      end
    end
  end
end

# Rails-style controller
class UsersController < ApplicationController
  before_action :authenticate!, only: [:edit, :update, :destroy]

  # Index action
  def index
    @users = User.all
  end

  # Show action with params
  def show
    @user = User.find(params[:id])
  end

  # Create action with strong params
  def create
    @user = User.new(user_params)
    if @user.save
      redirect_to @user
    else
      render :new
    end
  end

  # Class method using def self.
  def self.default_per_page
    25
  end

  private

  # Strong parameters
  def user_params
    params.require(:user).permit(:name, :email, :password)
  end
end

# Rails-style model
class User < ApplicationRecord
  # Associations
  belongs_to :organization
  has_many :posts, dependent: :destroy
  has_many :comments, through: :posts

  # Validations
  validates :name, presence: true
  validates :email, presence: true, uniqueness: true

  # Scopes
  scope :active, -> { where(active: true) }
  scope :admins, -> { where(admin: true) }

  # Instance method
  def full_name
    "#{first_name} #{last_name}"
  end

  # Method with keyword arguments
  def greet(message: "Hello", formal: false)
    prefix = formal ? "Dear" : ""
    "#{prefix} #{message}, #{name}!"
  end

  # Method with splat
  def update_attributes(*args, **kwargs)
    super
  end

  # Class methods via class << self
  class << self
    def find_by_email(email)
      find_by(email: email.downcase)
    end

    def create_guest
      create(name: "Guest", email: "guest@example.com")
    end
  end
end

# Simple class without inheritance
class Calculator
  # Constructor
  def initialize(value = 0)
    @value = value
  end

  # Instance method with block
  def calculate(&block)
    block.call(@value) if block_given?
  end

  # Operator overloading
  def +(other)
    Calculator.new(@value + other.to_i)
  end
end

# Top-level method
def standalone_helper
  "I am a helper method"
end

# Another top-level method with params
def format_currency(amount, currency: "USD")
  "#{currency} #{amount}"
end
