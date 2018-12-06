<!-- this place will show the actual contents of the blackboard. 
It will be reloaded automatically from the server -->
<div id="boardcontents_placeholder">
	<!-- The title comes here -->
	<div id="boardtitle_placeholder" class="boardtitle">{{board_title}}</div>
    <input type="text" name="id" value="ID" readonly>
    <input type="text" name="entry" value="Entry" size="70%%" readonly>
    % for board_entry in range(0, len(board_dict)):
	    % for board_element in board_dict[board_entry]:
			<form class="entryform" target="noreload-form-target" method="post" action="/board/{{board_entry}}/">
				<input type="text" name="id" value="{{board_entry}}" readonly>
				<input type="text" name="entry" value="{{board_element[1]}}" size="70%%">
				<input type="text" name="node_id" value="{{board_element[0]}}" size="70%%" readonly>
				<button type="submit" name="delete" value="0">Modify</button>
				<button type="submit" name="delete" value="1">X</button>
			</form>
	    %end
    %end
</div>
