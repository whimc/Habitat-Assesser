package edu.whimc.habitat_assesser;

import com.corundumstudio.socketio.Configuration;
import com.corundumstudio.socketio.SocketIOClient;
import com.corundumstudio.socketio.SocketIOServer;

import edu.whimc.overworld_agent.OverworldAgent;
import edu.whimc.habitat_assesser.utils.sql.Queryer;
import edu.whimc.habitat_assesser.socket.AssessmentResponse;

import java.util.*;

import org.bukkit.Bukkit;
import org.bukkit.command.PluginCommand;
import org.bukkit.entity.Player;
import org.bukkit.plugin.java.JavaPlugin;
import edu.whimc.overworld_agent.dialoguetemplate.events.BuildAssessEvent;

public final class HabitatAssesser extends JavaPlugin {

    private final Queue<BuildAssessEvent> assessmentQueue = new LinkedList<>();
    private SocketIOServer socketServer;
    private OverworldAgent agentPlugin;
    private Queryer queryer;

    @Override
    public void onEnable() {
        super.saveDefaultConfig();

        this.queryer = new Queryer(this, q -> {
            // If we couldn't connect to the database disable the plugin
            if (q == null) {
                this.getLogger().severe("Could not establish MySQL connection! Disabling plugin...");
                return;
            }

        });

        this.agentPlugin = (OverworldAgent) getServer().getPluginManager().getPlugin("WHIMC-OverworldAgent");

        //Set up habitat socket server
        Configuration configHabitats = new Configuration();
        configHabitats.setHostname(super.getConfig().getString("websocket.habitat_assessment.host"));
        configHabitats.setPort(super.getConfig().getInt("websocket.habitat_assessment.port"));
        this.socketServer = new SocketIOServer(configHabitats);
        UUID uuid = UUID.randomUUID();
        this.socketServer.addConnectListener(client -> {
            client.set("uuid", uuid);
            client.sendEvent("uuid", uuid);
            this.getLogger().info("connected to " + client.getRemoteAddress() + " [" + uuid + "]");
        });

        socketServer.addEventListener("assessment_response", AssessmentResponse.class, (client, response, ackRequest) -> {
            queryer.storeNewBuildAssessment(response, id -> {
                String feedback = "Nice work on " + super.getConfig().getString("habitat_feedback." + response.getHighestCategory()) + ", have you thought about working on " + super.getConfig().getString("habitat_feedback." + response.getLowestCategory()) + "?";
                Map<String, Double> sortedScoresAdj = response.getPriorityAdjScores();
                this.getLogger().info("Interaction ID: " + response.getId());
                this.getLogger().info("User: " + response.getUser());
                this.getLogger().info("Feedback: " + feedback);

                Player player = Bukkit.getPlayer(response.getUser());
                if (player == null) {
                    return;
                }

                Utils.msg(player, "&m                                                                                 ");
                Utils.msg(player, "&b&lYour habitat has been analyzed!");
                Utils.msg(player, "");
                Utils.msg(player, "Scores: &c0 = needs improvement, &e1-1.5 = good, &a2-3 = excellent");
                for(String key : sortedScoresAdj.keySet()){
                    Double score = sortedScoresAdj.get(key);
                    if(score >= 2){
                        Utils.msg(player, "&a" + key + " : " + score);
                    } else if(score >= 1) {
                        Utils.msg(player, "&e" + key + " : " + score);
                    } else {
                        Utils.msg(player, "&c" + key + " : " + score);
                    }
                }
                Utils.msg(player, "&e&lFEEDBACK:");
                Utils.msg(player, "    &6" + feedback);
                Utils.msg(player, "");
                Utils.msg(player, "&m                                                                                 ");
            });
        });

        socketServer.start();

        // Queue up some events
        Bukkit.getScheduler().scheduleSyncRepeatingTask(this, () -> {
            if (this.assessmentQueue.isEmpty()) {
                return;
            }
            Bukkit.getScheduler().runTaskAsynchronously(this, () -> {
                for (SocketIOClient client : this.getSocketServer().getAllClients()) {
                    BuildAssessEvent assessment = this.assessmentQueue.poll();
                    client.sendEvent("assess", assessment.getId(), assessment.getUser(), assessment.getWorld(), assessment.getTeammates());
                    break;
                }
            });
        }, 20, 20);

        getServer().getPluginManager().registerEvents(new Listeners(this), this);

        PluginCommand cmd = getCommand("habitats");
        AssessmentCommand assessCommand = new AssessmentCommand(this);
        cmd.setExecutor(assessCommand);
        cmd.setTabCompleter(assessCommand);
    }

    @Override
    public void onDisable() {
        this.socketServer.stop();
    }

    public void queueAssessment(BuildAssessEvent assessEvent) {
        this.assessmentQueue.add(assessEvent);
    }

    public Queue<BuildAssessEvent> getAssessmentQueue() {
        return this.assessmentQueue;
    }

    public SocketIOServer getSocketServer() {
        return this.socketServer;
    }
    public OverworldAgent getAgentPlugin(){return this.agentPlugin;}

    public Optional<SocketIOClient> getClient(UUID clientUuid) {
        return this.socketServer.getAllClients().stream()
                .filter(c -> c.get("uuid").equals(clientUuid))
                .findFirst();
    }

}
