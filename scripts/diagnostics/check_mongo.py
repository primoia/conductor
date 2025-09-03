#!/usr/bin/env python3
"""
Test script to verify MongoDB configuration
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

from core.state_repository import MongoStateRepository


def test_mongo_connection():
    """Tests connection and basic operations with MongoDB."""

    print("🔍 Verifying MongoDB configuration...")

    # Check environment variable
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        print("❌ MONGO_URI not configured!")
        print("   Configure with: export MONGO_URI='mongodb://localhost:27017'")
        return False

    print(f"📝 MONGO_URI: {mongo_uri}")

    try:
        # Create repository (tests connection)
        print("🔌 Testing connection...")
        repo = MongoStateRepository()
        print("✅ Connection established successfully!")

        # Test data
        agent_home_path = "/test/mongo"
        state_file_name = "test_state.json"
        test_data = {
            "conversation_history": [
                {"role": "user", "message": "MongoDB Test"},
                {"role": "assistant", "message": "MongoDB working!"},
            ],
            "agent_id": "TestAgent",
            "timestamp": "2024-01-01T00:00:00",
        }

        print("💾 Testing save...")
        save_result = repo.save_state(agent_home_path, state_file_name, test_data)
        if save_result:
            print("✅ Data saved successfully!")
        else:
            print("❌ Failed to save data!")
            return False

        print("📖 Testing load...")
        loaded_data = repo.load_state(agent_home_path, state_file_name)

        # Verify if data was loaded correctly
        if loaded_data.get("agent_id") == test_data["agent_id"]:
            print("✅ Data loaded successfully!")
            print(f"   Agent ID: {loaded_data['agent_id']}")
            print(f"   Messages: {len(loaded_data['conversation_history'])}")
            print(f"   Repository type: {loaded_data.get('repository_type', 'N/A')}")
        else:
            print("❌ Data loaded incorrectly!")
            return False

        # Close connection
        repo.close()
        print("🔚 Connection closed.")

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Install pymongo: pip install pymongo")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def show_mongo_examples():
    """Shows MongoDB configuration examples."""

    print("\n📋 MongoDB_URI configuration examples:")
    print("=" * 50)

    print("\n1. Local MongoDB (no authentication):")
    print("   export MONGO_URI='mongodb://localhost:27017'")

    print("\n2. Local MongoDB (with authentication):")
    print("   export MONGO_URI='mongodb://user:pass@localhost:27017/conductor_db'")

    print("\n3. MongoDB Docker:")
    print("   docker run -d --name mongodb -p 27017:27017 mongo:latest")
    print("   export MONGO_URI='mongodb://localhost:27017'")

    print("\n4. MongoDB Atlas (cloud):")
    print(
        "   export MONGO_URI='mongodb+srv://user:pass@cluster.mongodb.net/conductor_db'"
    )

    print("\n📊 Data structure in MongoDB:")
    print("   Database: conductor_state (default)")
    print("   Collection: agent_states (default)")
    print("   Document ID: {agent_home_path}_{state_file_name}")

    print("\n🔧 Useful commands:")
    print("   # View saved data via mongo shell")
    print("   mongo")
    print("   use conductor_state")
    print("   db.agent_states.find().pretty()")


if __name__ == "__main__":
    print("🧪 MongoDB Configuration Test")
    print("=" * 40)

    if test_mongo_connection():
        print("\n🎉 MongoDB configured and working!")
    else:
        print("\n💡 Configuration needed:")
        show_mongo_examples()