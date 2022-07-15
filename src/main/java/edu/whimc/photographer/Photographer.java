package edu.whimc.photographer;

import com.gmail.filoghost.holographicdisplays.api.Hologram;
import com.corundumstudio.socketio.Configuration;
import com.corundumstudio.socketio.SocketIOClient;
import com.corundumstudio.socketio.SocketIOServer;
import edu.whimc.observations.models.ObserveEvent;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import org.apache.commons.lang.StringUtils;
import org.bukkit.Bukkit;
import org.bukkit.command.Command;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.plugin.java.JavaPlugin;

public final class Photographer extends JavaPlugin implements Listener {

    private SocketIOServer server;
    private Map<UUID, UUID> photographers = new HashMap<>();

    @Override
    public void onEnable() {
        super.saveDefaultConfig();

        Configuration config = new Configuration();
        config.setHostname(super.getConfig().getString("websocket.host"));
        config.setPort(super.getConfig().getInt("websocket.port"));

        this.server = new SocketIOServer(config);
        this.server.addConnectListener(client -> {
            UUID uuid = UUID.randomUUID();
            client.set("uuid", uuid);
            client.sendEvent("uuid", uuid);
            Bukkit.broadcastMessage("connected to " + client.getRemoteAddress() + " [" + uuid + "]");
        });

        this.server.addDisconnectListener(
                client -> Bukkit.broadcastMessage("disconnected " + client.getRemoteAddress()));

        server.addEventListener("test", String.class,
                (client, message, ackRequest) -> {
                    Bukkit.broadcastMessage(client.getRemoteAddress() + " [" + client.get("uuid") + "]: " + message);
                });

        this.server.start();

        getServer().getPluginManager().registerEvents(this, this);
    }

    @EventHandler
    public void onObservation(ObserveEvent event) {
        for (UUID uuid : this.photographers.keySet()) {
            Player player = Bukkit.getPlayer(uuid);
            if (player == null) {
                continue;
            }

            player.sendMessage("An observation has been made! Teleporting you to take a picture in 5 second");

            Bukkit.getScheduler().runTaskLater(this, () -> {
                Hologram hologram = event.getObservation().getHologram();
                hologram.getVisibilityManager().hideTo(player);
                player.teleport(event.getObservation().getViewLocation());

                UUID clientUuid = this.photographers.get(player.getUniqueId());
                SocketIOClient client = getClient(clientUuid);

                client.sendEvent("screenshot");
            }, 20 * 5);
        }
    }

    @Override
    public void onDisable() {
        this.server.stop();
    }

    @Override
    public boolean onCommand(CommandSender sender, Command command, String label, String[] args) {
        if (args.length == 0) {
            sender.sendMessage("/photographer clients");
            sender.sendMessage("/photographer collect <uuid>");
            sender.sendMessage("/photographer send <uuid> <msg>");
            return true;
        }

        String subCmd = args[0];

        if (subCmd.equalsIgnoreCase("clients")) {
            sender.sendMessage("Clients:");
            for (SocketIOClient client : this.server.getAllClients()) {
                sender.sendMessage(client.toString());
            }

            return true;
        }

        if (args.length < 2) {
            return true;
        }

        UUID uuid = UUID.fromString(args[1]);
        SocketIOClient client = getClient(uuid);

        if (client == null) {
            sender.sendMessage("Client not found");
            return true;
        }

        if (subCmd.equalsIgnoreCase("collect")) {
            if (!(sender instanceof Player)) {
                sender.sendMessage("You have to be a player");
            }
            Player player = (Player) sender;
            player.sendMessage("You have become a photographer for uuid!");
            this.photographers.put(player.getUniqueId(), client.get("uuid"));
            return true;
        }

        if (subCmd.equalsIgnoreCase("send")) {
            if (args.length <= 2) {
                sender.sendMessage("/photographer send <uuid> <msg>");
                return true;
            }

            String message = StringUtils.join(args, " ", 2, args.length);
            Bukkit.getScheduler().runTaskAsynchronously(this, () -> {
                client.sendEvent("test", message);
                client.sendEvent("nothing");
            });
            return true;
        }

//        this.server.getBroadcastOperations().sendEvent("test", new VoidAckCallback() {
//            @Override
//            protected void onSuccess() {
//                Bukkit.broadcastMessage("done!");
//            }
//        }, "test");

        return true;
    }

    private SocketIOClient getClient(UUID clientUuid) {
        for (SocketIOClient client : this.server.getAllClients()) {
            if (client.get("uuid").equals(clientUuid)) {
                return client;
            }
        }

        return null;
    }
}
