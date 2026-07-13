"""End-to-end test for the generic pipeline framework with NEOS environment.

This script tests the generic pipeline framework using the existing NEOS
database models and handlers.
"""

import asyncio
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# Import framework components
from neos_agent.skills.pipeline_schema import load_pipeline_config_from_yaml
from neos_agent.skills.pipeline_executor import PipelineExecutor
from neos_agent.agent.tool_registry import ToolRegistry, create_composed_registry
from neos_agent.agent.neos_handlers import NEOS_HANDLERS

# Import NEOS models
from neos_agent.db.models import Base, Ecosystem


async def setup_test_database():
    """Set up test database with an ecosystem."""
    # Use SQLite for testing
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=True)
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session factory
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    return async_session


async def create_test_ecosystem(session: AsyncSession) -> uuid.UUID:
    """Create a test ecosystem."""
    ecosystem = Ecosystem(
        id=uuid.uuid4(),
        name="Test Ecosystem",
        description="Test ecosystem for pipeline framework testing",
        status="active",
    )
    
    session.add(ecosystem)
    await session.commit()
    await session.refresh(ecosystem)
    
    print(f"Created test ecosystem: {ecosystem.name} (ID: {ecosystem.id})")
    return ecosystem.id


async def test_pipeline_execution():
    """Run end-to-end test of pipeline execution."""
    print("=" * 60)
    print("Generic Pipeline Framework - End-to-End Test")
    print("=" * 60)
    
    # Setup database
    print("\n1. Setting up test database...")
    async_session = await setup_test_database()
    
    async with async_session() as session:
        # Create test ecosystem
        print("\n2. Creating test ecosystem...")
        ecosystem_id = await create_test_ecosystem(session)
        
        # Load pipeline configuration
        print("\n3. Loading pipeline configuration...")
        pipeline_path = Path(__file__).parent / "test_pipeline.yaml"
        yaml_content = pipeline_path.read_text()
        
        config, errors = load_pipeline_config_from_yaml(yaml_content)
        if errors:
            print(f"❌ Failed to load pipeline: {errors}")
            return False
        
        print(f"✅ Loaded pipeline: {config.target_tool.name}")
        print(f"   Description: {config.target_tool.description}")
        print(f"   Steps: {len(config.target_tool.pipeline)}")
        
        # Create executor with NEOS handlers
        print("\n4. Creating pipeline executor with NEOS handlers...")
        scope = {
            "ecosystem_ids": [ecosystem_id],
            "tenant_id": str(ecosystem_id),
        }
        
        executor = PipelineExecutor(session, scope=scope)
        
        # Register NEOS handlers
        for op, handler in NEOS_HANDLERS.items():
            executor.register_handler(op, handler)
            print(f"   Registered handler: {op}")
        
        # Execute pipeline
        print("\n5. Executing pipeline...")
        test_args = {
            "display_name": "Test Member",
            "member_id": str(uuid.uuid4()),
        }
        
        print(f"   Input args: {test_args}")
        
        result = await executor.execute(config, test_args)
        
        print("\n6. Pipeline execution result:")
        if result["success"]:
            print("✅ Pipeline executed successfully")
            print(f"   Tool: {result.get('tool')}")
            print(f"   Data: {result.get('data')}")
            
            # Verify the member was created
            print("\n7. Verifying database state...")
            from neos_agent.db.models import Member
            from sqlalchemy import select
            
            stmt = select(Member).where(Member.display_name == "Test Member")
            db_result = await session.execute(stmt)
            member = db_result.scalars().first()
            
            if member:
                print(f"✅ Member found in database:")
                print(f"   ID: {member.id}")
                print(f"   Member ID: {member.member_id}")
                print(f"   Display Name: {member.display_name}")
                print(f"   Status: {member.current_status}")
                print(f"   Ecosystem ID: {member.ecosystem_id}")
                return True
            else:
                print("❌ Member not found in database")
                return False
        else:
            print(f"❌ Pipeline execution failed")
            print(f"   Error: {result.get('error')}")
            if "step" in result:
                print(f"   Failed at step: {result['step']}")
            if "field" in result:
                print(f"   Field: {result['field']}")
            return False


async def test_tool_registry():
    """Test the tool registry integration."""
    print("\n" + "=" * 60)
    print("Testing Tool Registry Integration")
    print("=" * 60)
    
    # Setup database
    print("\n1. Setting up test database...")
    async_session = await setup_test_database()
    
    async with async_session() as session:
        # Create test ecosystem
        print("\n2. Creating test ecosystem...")
        ecosystem_id = await create_test_ecosystem(session)
        
        # Create tool registry with NEOS handlers
        print("\n3. Creating tool registry...")
        registry = create_composed_registry(handler_registry=NEOS_HANDLERS)
        
        # Load and register pipeline config
        print("\n4. Loading and registering pipeline...")
        pipeline_path = Path(__file__).parent / "test_pipeline.yaml"
        yaml_content = pipeline_path.read_text()
        
        config, errors = load_pipeline_config_from_yaml(yaml_content)
        if errors:
            print(f"❌ Failed to load pipeline: {errors}")
            return False
        
        registry.register_from_config(config)
        
        print(f"✅ Registered tool: {config.target_tool.name}")
        print(f"   Total tools in registry: {len(registry.get_all_tools())}")
        
        # Execute tool through registry
        print("\n5. Executing tool through registry...")
        scope = {
            "ecosystem_ids": [ecosystem_id],
        }
        
        test_args = {
            "display_name": "Registry Test Member",
            "member_id": str(uuid.uuid4()),
        }
        
        result = await registry.execute_tool(
            config.target_tool.name,
            test_args,
            session,
            scope
        )
        
        print("\n6. Registry execution result:")
        if result["success"]:
            print("✅ Tool executed successfully through registry")
            print(f"   Data: {result.get('data')}")
            return True
        else:
            print(f"❌ Tool execution failed")
            print(f"   Error: {result.get('error')}")
            return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("GENERIC PIPELINE FRAMEWORK - END-TO-END TEST SUITE")
    print("=" * 60)
    
    # Test 1: Direct pipeline execution
    test1_success = await test_pipeline_execution()
    
    # Test 2: Tool registry integration
    test2_success = await test_tool_registry()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Pipeline Execution Test: {'✅ PASSED' if test1_success else '❌ FAILED'}")
    print(f"Tool Registry Test: {'✅ PASSED' if test2_success else '❌ FAILED'}")
    
    if test1_success and test2_success:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
