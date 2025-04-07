"""
Tests for the network service.
"""

import asyncio
import pytest
from core.network.network_service import NetworkService

@pytest.fixture
async def network_service():
    """Create a network service instance."""
    service = NetworkService()
    yield service
    # Cleanup
    await service.stop_server()

@pytest.mark.asyncio
async def test_network_service_start_stop(network_service: NetworkService):
    """Test starting and stopping the server."""
    # Start server
    await network_service.start_server("127.0.0.1", 0)  # Port 0 = random available port
    assert network_service._server is not None
    
    # Stop server
    await network_service.stop_server()
    assert network_service._server is None

@pytest.mark.asyncio
async def test_network_service_client_connection(network_service: NetworkService):
    """Test client connections."""
    # Start server
    server_port = 8888
    await network_service.start_server("127.0.0.1", server_port)
    
    # Connect client
    reader, writer = await asyncio.open_connection("127.0.0.1", server_port)
    
    # Wait for client to be registered
    await asyncio.sleep(0.1)
    
    # Check client is connected
    clients = await network_service.get_connected_clients()
    assert len(clients) == 1
    client_id = list(clients)[0]
    
    # Get client info
    client_info = await network_service.get_client_info(client_id)
    assert client_info is not None
    assert client_info["id"] == client_id
    
    # Cleanup
    writer.close()
    await writer.wait_closed()
    await network_service.stop_server()

@pytest.mark.asyncio
async def test_network_service_message_sending(network_service: NetworkService):
    """Test sending messages between server and client."""
    # Start server
    server_port = 8889
    await network_service.start_server("127.0.0.1", server_port)
    
    # Connect client
    reader, writer = await asyncio.open_connection("127.0.0.1", server_port)
    
    # Wait for client to be registered
    await asyncio.sleep(0.1)
    client_id = list(await network_service.get_connected_clients())[0]
    
    # Send message to client
    test_message = b"Hello client!"
    success = await network_service.send_to_client(client_id, test_message)
    assert success
    
    # Receive message
    received = await reader.read(100)
    assert received == test_message
    
    # Send message from client
    test_message = b"Hello server!"
    writer.write(test_message)
    await writer.drain()
    
    # Get client stream and verify message
    stream = network_service.get_client_stream(client_id)
    assert stream is not None
    
    async for message in stream:
        assert message == test_message
        break
    
    # Cleanup
    writer.close()
    await writer.wait_closed()
    await network_service.stop_server()

@pytest.mark.asyncio
async def test_network_service_broadcast(network_service: NetworkService):
    """Test broadcasting messages to all clients."""
    # Start server
    server_port = 8890
    await network_service.start_server("127.0.0.1", server_port)
    
    # Connect multiple clients
    client1_reader, client1_writer = await asyncio.open_connection("127.0.0.1", server_port)
    client2_reader, client2_writer = await asyncio.open_connection("127.0.0.1", server_port)
    
    # Wait for clients to be registered
    await asyncio.sleep(0.1)
    clients = await network_service.get_connected_clients()
    assert len(clients) == 2
    
    # Broadcast message
    test_message = b"Broadcast test"
    await network_service.broadcast(test_message)
    
    # Verify both clients received the message
    received1 = await client1_reader.read(100)
    received2 = await client2_reader.read(100)
    assert received1 == test_message
    assert received2 == test_message
    
    # Cleanup
    client1_writer.close()
    client2_writer.close()
    await client1_writer.wait_closed()
    await client2_writer.wait_closed()
    await network_service.stop_server()

@pytest.mark.asyncio
async def test_network_service_client_disconnect(network_service: NetworkService):
    """Test client disconnection handling."""
    # Start server
    server_port = 8891
    await network_service.start_server("127.0.0.1", server_port)
    
    # Connect client
    reader, writer = await asyncio.open_connection("127.0.0.1", server_port)
    
    # Wait for client to be registered
    await asyncio.sleep(0.1)
    clients = await network_service.get_connected_clients()
    assert len(clients) == 1
    client_id = list(clients)[0]
    
    # Disconnect client
    success = await network_service.disconnect_client(client_id)
    assert success
    
    # Verify client is disconnected
    clients = await network_service.get_connected_clients()
    assert len(clients) == 0
    
    # Cleanup
    await network_service.stop_server()
