package edu.whimc.photographer;

import com.corundumstudio.socketio.Configuration;
import com.corundumstudio.socketio.SocketIOClient;
import com.corundumstudio.socketio.SocketIOServer;
import com.gmail.filoghost.holographicdisplays.api.Hologram;
import com.gmail.filoghost.holographicdisplays.api.HologramsAPI;
import edu.whimc.observations.Observations;
import edu.whimc.observations.models.Observation;
import edu.whimc.observations.models.ObserveEvent;
import edu.whimc.photographer.socket.Response;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;
import org.apache.commons.lang.StringUtils;
import org.bukkit.Bukkit;
import org.bukkit.ChatColor;
import org.bukkit.command.Command;
import org.bukkit.command.CommandSender;
import org.bukkit.command.TabCompleter;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.plugin.java.JavaPlugin;

public final class Photographer extends JavaPlugin implements Listener, TabCompleter {

    private SocketIOServer server;
    private final Map<UUID, UUID> photographers = new HashMap<>();
    private Observations observationsPlugin;

    @Override
    public void onEnable() {
        super.saveDefaultConfig();

        Configuration config = new Configuration();
        config.setHostname(super.getConfig().getString("websocket.host"));
        config.setPort(super.getConfig().getInt("websocket.port"));

        this.observationsPlugin = (Observations) getServer().getPluginManager().getPlugin("WHIMC-Observations");

        this.server = new SocketIOServer(config);
        this.server.addConnectListener(client -> {
            UUID uuid = UUID.randomUUID();
            client.set("uuid", uuid);
            client.sendEvent("uuid", uuid);
            Bukkit.broadcastMessage("connected to " + client.getRemoteAddress() + " [" + uuid + "]");
        });

        this.server.addDisconnectListener(
                client -> Bukkit.broadcastMessage("disconnected " + client.getRemoteAddress()));

        server.addEventListener("test", String.class, (client, message, ackRequest) ->
            Bukkit.broadcastMessage(client.getRemoteAddress() + " [" + client.get("uuid") + "]: " + message)
        );

        server.addEventListener("screenshot_response", Response.class, (client, response, ackRequest) -> {
            Bukkit.broadcastMessage("Observation ID: " + response.getObservationId());
            Bukkit.broadcastMessage("Feedback: " + response.getFeedback());
            Bukkit.broadcastMessage("Generated caption: " + response.getGeneratedCaption());
            Bukkit.broadcastMessage("Score: " + response.getScore());
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

            player.sendMessage("An observation has been made! Teleporting you to take a picture in 3 seconds");

            Bukkit.getScheduler().runTaskLater(this, () -> {
                Observation observation = event.getObservation();

                // Make the observation invisible
                for (Hologram hologram : HologramsAPI.getHolograms(this.observationsPlugin)) {
                    hologram.getVisibilityManager().hideTo(player);
                }
                player.teleport(observation.getViewLocation());

                UUID clientUuid = this.photographers.get(player.getUniqueId());
                SocketIOClient client = getClient(clientUuid);

                String strippedObservation = ChatColor.stripColor(observation.getObservation());

                player.sendMessage("Taking picture in 5 seconds");
                Bukkit.getScheduler().runTaskLaterAsynchronously(this, () -> {
                    client.sendEvent("screenshot", observation.getId(), strippedObservation);
                }, 20 * 5);

            }, 20 * 3);
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
                sender.sendMessage(client.getRemoteAddress() + ": " + client.get("uuid"));
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
            player.sendMessage("You have become a photographer for " + client.get("uuid"));
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
                client.sendEvent("message", message);
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

    @Override
    public List<String> onTabComplete(CommandSender sender, Command command, String alias, String[] args) {
        return this.server.getAllClients().stream()
                .map(client-> client.get("uuid").toString())
                .collect(Collectors.toList());
    }
}
